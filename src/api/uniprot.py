# src/api/uniprot.py
"""UniProt REST API クライアント（レスポンス取得のみ担当）。"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from api.base import ApiResponse, BaseApiConfig, BaseJsonApiClient


@dataclass
class UniprotApiConfig(BaseApiConfig):
    """UniProt REST API のコンフィグクラス"""

    api_base: str = "https://rest.uniprot.org/uniprotkb"


class UniprotApiClients(BaseJsonApiClient):
    """UniProt REST API を叩くクライアント"""

    def __init__(
        self,
        config: UniprotApiConfig | None = None,
        session: requests.Session | None = None,
    ):
        super().__init__(config=config or UniprotApiConfig(), session=session)

    def _search_params(self, accession: str) -> dict[str, Any]:
        """`/uniprotkb/search` のパラメータ構築（``fields`` は付けず、必要な情報は body から後段で抽出）。"""
        return {"query": f"accession:{accession}", "format": "json"}

    def get_search_response(self, accession: str) -> ApiResponse:
        """`/uniprotkb/search` のレスポンスを取得"""
        acc = self.normalize_accession(accession)
        url = self._construct_url(endpoint=f"search")
        params = self._search_params(acc)
        return self._get_response_with_retry(url=url, params=params)

    def save_search_response_body_json(
        self,
        accession: str,
        output_path: str | Path,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """検索レスポンスを取得し、``body`` を JSON ファイルに保存する。"""
        resp = self.get_search_response(accession)
        return self.save_response_body_json(
            resp,
            output_path,
            indent=indent,
            ensure_ascii=ensure_ascii,
        )
