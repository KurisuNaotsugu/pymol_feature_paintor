# src/services/alphafold_extractor.py
"""AlphaFold DB: ``ApiResponse`` / body から構造 URL・配列を抽出する"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from api.base import ApiResponse
from core.api_response_validation import validate_api_response
from core.models import AminoAcidSequence

# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _validate_af_api_response(resp: ApiResponse, *, accession: str) -> None:
    """``ApiResponse`` のバリデーション"""
    validate_api_response(
        resp,
        api_name="AlphaFold DB",
        accession=accession,
        not_found_exc=RuntimeError,
        fetch_exc=RuntimeError,
        body="dict_or_list",
        append_snippet_on_fetch_error=True,
    )

# ------------------------------------------------------------
# クラス定義
# ------------------------------------------------------------
class AlphaFoldDBClient:
    """AlphaFold prediction API のメタデータから構造URL/format を抽出します。"""

    FORMAT_PREFERENCE: Tuple[str, ...] = ("cif", "pdb", "bcif")
    STRUCTURE_EXTENSIONS: Tuple[str, ...] = (".cif", ".bcif", ".pdb")
    FORMAT_TO_EXTENSION: Dict[str, str] = {"cif": "cif", "pdb": "pdb", "bcif": "bcif"}

    def extract_uniprot_sequence_from_body(self, body: Any) -> Optional[AminoAcidSequence]:
        """配列情報抽出
        
        Args:
            body: ApiResponse.body
        """
        if body is None:
            return None
        obj = body[0] if isinstance(body, list) and body else body
        if not isinstance(obj, dict):
            return None
        seq = obj.get("uniprotSequence") or obj.get("sequence")
        if isinstance(seq, str):
            return AminoAcidSequence(value=seq)
        return None

    def pick_structure_url(self, resp: ApiResponse, accession: str) -> Tuple[str, str]:
        """構造データURL抽出

        Args:
            resp: AlphaFold prediction API のレスポンス
            accession: UniProt accession（エラーメッセージ用）
        Returns:
            Tuple[str, str]: 構造URL/format (URL, format)
        """
        _validate_af_api_response(resp, accession=accession)

        # メタデータを抽出
        meta = resp.body
        obj = meta[0] if isinstance(meta, list) and meta else meta
        if not isinstance(obj, dict):
            raise RuntimeError("FetchError: Unexpected metadata format from AlphaFold API")

        # URL候補収集
        urls: list[str] = []
        for v in obj.values():
            if isinstance(v, str) and v.startswith("http"):
                urls.append(v)
        # 浅い探索で見つからない場合は深い探索
        if not urls:
            urls = self._walk_for_urls(obj)

        # 構造データURLだけ抽出
        struct_urls = [u for u in urls if any(ext in u.lower() for ext in self.STRUCTURE_EXTENSIONS)]
        if not struct_urls:
            raise RuntimeError("FetchError: Could not find any structure URLs in metadata (API may have changed)")

        def kind(u: str) -> str:
            ul = u.lower()
            for fmt in self.FORMAT_PREFERENCE:
                ext = f".{self.FORMAT_TO_EXTENSION[fmt]}"
                if ext in ul:
                    return fmt
            return "other"

        # prefer順に最初に見つかったURLを採用
        for p in list(self.FORMAT_PREFERENCE):
            for u in struct_urls:
                if kind(u) == p:
                    return u, p

        # 最後の保険
        u = struct_urls[0]
        return u, kind(u)

    def _walk_for_urls(self, d: Dict[str, Any]) -> list[str]:
        """ネストした dict/list を再帰的にたどり、構造ファイル用のURLを集めて返す"""
        found: list[str] = []
        stack: list[Any] = [d]
        while stack:
            cur = stack.pop()
            if isinstance(cur, dict):
                for v in cur.values():
                    stack.append(v)
            elif isinstance(cur, list):
                stack.extend(cur)
            elif isinstance(cur, str) and cur.startswith("http"):
                if any(ext in cur.lower() for ext in self.STRUCTURE_EXTENSIONS):
                    found.append(cur)
        return found
