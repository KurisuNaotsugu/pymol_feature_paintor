# src/services/uniprot_extractor.py
"""UniProt API から情報を抽出するクラス"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from core.api_response_validation import validate_api_response
from api.base import ApiResponse
from core.models import AminoAcidSequence

# ------------------------------------------------------------
# 例外クラス
# ------------------------------------------------------------
class UniProtNotFoundError(RuntimeError):
    """UniProt 側でアクセッションが見つからない場合の例外。"""

class UniProtFetchError(RuntimeError):
    """UniProt API の取得・レスポンス形式が期待と異なる場合の例外。"""


# ------------------------------------------------------------
# データクラス
# ------------------------------------------------------------
@dataclass(frozen=True)
class UniprotFeatures:
    """UniProt API の response から抽出した feature 情報
    
    Attributes:
        feature: feature名 (Topological domain, Transmembrane)
        location: location情報
        description: description情報 (Extracellular, Cytoplasmic, Helicalなど)
    """
    feature: str
    location: Any
    description: str


# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _validate_results(body: dict[str, Any], *, accession: str) -> None:
    """`body["results"]` が期待する形かを検証します。"""
    results = body.get("results")
    if not isinstance(results, list):
        raise UniProtFetchError(
            f"FetchError: UniProt API response results is not a list (accession={accession})"
        )
    if not results:
        raise UniProtNotFoundError(f"NotFoundError: UniProt: no entry for accession: {accession}")
    entry = results[0]
    if not isinstance(entry, dict):
        raise UniProtFetchError(
            f"FetchError: UniProt API results[0] is not a dict (accession={accession})"
        )

# ------------------------------------------------------------
# クラス定義
# ------------------------------------------------------------
class UniprotExtractor:
    """UniProt の response body から情報を抽出するクラス"""

    def _validate_uniprot_search_api_response(self, resp: ApiResponse, *, accession: str) -> None:
        """UniProt ``/search`` の ``ApiResponse`` を想定: 404 / 非2xx / JSONオブジェクト body を確認する。"""
        validate_api_response(
            resp,
            api_name="UniProt",
            accession=accession,
            not_found_exc=UniProtNotFoundError,
            fetch_exc=UniProtFetchError,
            body="dict",
        )

    def extract_sequence(self, resp: ApiResponse, *, accession: str) -> AminoAcidSequence:
        """UniProt API の response からアミノ酸配列を抽出
        
        Args:
            resp: UniProt API の response
            accession: UniProt accession
        """
        self._validate_uniprot_search_api_response(resp, accession=accession)
        _validate_results(resp.body, accession=accession)
        entry = resp.body["results"][0]
        seq_obj = entry.get("sequence")
        if not isinstance(seq_obj, dict) or "value" not in seq_obj:
            raise UniProtFetchError("FetchError: UniProt API response missing sequence.value")
        return AminoAcidSequence(value=seq_obj["value"])

    def extract_features(self, resp: ApiResponse, *, accession: str) -> List[UniprotFeatures]:
        """UniProt API の response から feature を抽出し、件ごとに ``UniprotFeatures`` に格納する。

        Args:
            resp: UniProt API の response
            accession: UniProt accession
        Returns:
            各要素が 1 feature の ``UniprotFeatures`` のリスト（空の場合あり）
        """
        self._validate_uniprot_search_api_response(resp, accession=accession)
        _validate_results(resp.body, accession=accession)
        entry = resp.body["results"][0]
        raw = entry.get("features") or []
        if not isinstance(raw, list):
            raise UniProtFetchError("FetchError: UniProt API response features is not a list")
        # feature 情報を抽出
        feature_list: list[UniprotFeatures] = []
        for i, f in enumerate(raw):
            if not isinstance(f, dict):
                raise UniProtFetchError(
                    f"FetchError: UniProt API response features[{i}] is not a dict"
                )
            ftype = f.get("type")
            feat_name = str(ftype) if ftype is not None else ""
            d = f.get("description")
            description = d.strip() if isinstance(d, str) else ""
            feature_list.append(
                UniprotFeatures(
                    feature=feat_name,
                    location=f.get("location"),
                    description=description,
                )
            )
        return feature_list

