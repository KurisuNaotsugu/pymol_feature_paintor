# src/api/alphafold.py
"""AlphaFold DB API: HTTP クライアントと構造ファイル取得（キャッシュ + ダウンロード）。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests

from api.base import ApiResponse, BaseApiConfig, BaseJsonApiClient
from core.cache import default_cache_dir
from core.http import make_session
from core.models import StructureArtifact
from services.alphafold_extractor import AlphaFoldDBClient


@dataclass
class AlphaFoldApiConfig(BaseApiConfig):
    """AlphaFold DB API のコンフィグクラス"""

    api_base: str = "https://alphafold.ebi.ac.uk/api"


class AlphafoldApiClient(BaseJsonApiClient):
    """AlphaFold DB の prediction エンドポイントを叩くクライアント"""

    def __init__(
        self,
        config: AlphaFoldApiConfig | None = None,
        session: requests.Session | None = None,
    ):
        super().__init__(config=config or AlphaFoldApiConfig(), session=session)

    def get_prediction(self, accession: str) -> ApiResponse:
        """Prediction API のレスポンスを取得

        Args:
            accession: UniProt accession
        """
        acc = self.normalize_accession(accession)
        url = self._construct_url(endpoint=f"prediction/{acc}")
        return self._get_response_with_retry(url)

    def save_prediction_body_json(
        self,
        accession: str,
        output_path: str | Path,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """Prediction API のレスポンスを取得し、``body`` を JSON ファイルに保存する。"""
        resp = self.get_prediction(accession)
        return self.save_response_body_json(
            resp,
            output_path,
            indent=indent,
            ensure_ascii=ensure_ascii,
        )


class AlphaFoldDBFetcherClient:
    """AlphaFold DB API を叩いて構造ファイルを取得（キャッシュ + ダウンロード）します。"""

    def __init__(
        self,
        *,
        api_config: Optional[AlphaFoldApiConfig] = None,
        cache_dir: Optional[Path] = None,
        session: Any | None = None,
    ):
        """ 初期化
        キャッシュディレクトリとHTTPセッションを設定
        Args:
            api_config: AlphaFold API のコンフィグ
            cache_dir: キャッシュディレクトリ
            session: HTTP セッション
        """
        self.session = session or make_session()
        self.cache_dir = cache_dir or default_cache_dir()
        self._api = AlphafoldApiClient(
            config=api_config or AlphaFoldApiConfig(),
            session=self.session,
        )
        self._extractor = AlphaFoldDBClient()

    def fetch_structure(
        self,
        accession: str,
        force: bool = False,
    ) -> StructureArtifact:
        """構造ファイルを取得
        Args:
            accession: UniProt accession
            force: キャッシュが存在する場合でもダウンロードするかどうか
        Returns:
            StructureArtifact: 構造ファイルの情報
        """
        acc = self._api.normalize_accession(accession)

        # キャッシュチェック
        for p in self._extractor.FORMAT_PREFERENCE:
            if p not in self._extractor.FORMAT_TO_EXTENSION:
                continue
            fmt = self._extractor.FORMAT_TO_EXTENSION[p]
            local = self._local_path(acc, fmt)
            if local.exists() and not force:
                return StructureArtifact(
                    accession=acc,
                    format=fmt,
                    local_path=local,
                    source_url="",
                )

        # キャッシュがない場合はprediction API を叩きます。
        resp = self._api.get_prediction(acc)
        url, fmt = self._extractor.pick_structure_url(resp, acc)

        local = self._local_path(acc, fmt)
        self._download(url, local)
        return StructureArtifact(
            accession=acc,
            format=fmt,
            local_path=local,
            source_url=url,
        )

    def _local_path(self, acc: str, fmt: str) -> Path:
        """キャッシュパスを決定

        Args:
            acc: UniProt accession
            fmt: ファイル形式
        Returns:
            Path: キャッシュパス
        """
        sub = self.cache_dir / "alphafold"
        sub.mkdir(parents=True, exist_ok=True)
        ext = self._extractor.FORMAT_TO_EXTENSION[fmt]
        return sub / f"AF_{acc}.{ext}"

    def check_structure_url_reachable(self, url: str) -> bool:
        """構造ファイル URL が応答するか軽量に確認する
        """
        timeout_sec = getattr(self._api.config, "timeout_sec", 60)
        try:
            r = self.session.head(url, allow_redirects=True, timeout=timeout_sec)
            if r.ok:
                return True
        except requests.RequestException:
            pass
        try:
            with self.session.get(url, stream=True, timeout=timeout_sec) as r:
                return r.ok
        except requests.RequestException:
            return False

    def _download(self, url: str, out_path: Path) -> None:
        """構造ファイルをダウンロード
        Args:
            url: ダウンロードするURL
            out_path: ダウンロード先のパス
        """
        out_path.parent.mkdir(parents=True, exist_ok=True)
        timeout_sec = getattr(self._api.config, "timeout_sec", 60)
        with self.session.get(url, stream=True, timeout=timeout_sec) as r:
            if not r.ok:
                raise RuntimeError(f"FetchError: Download failed {r.status_code}: {url}")
            tmp = out_path.with_suffix(out_path.suffix + ".part")
            with tmp.open("wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 256):
                    if chunk:
                        f.write(chunk)
            tmp.replace(out_path)
