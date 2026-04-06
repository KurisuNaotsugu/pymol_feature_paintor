# src/api/pipeline.py
"""UniProt accession に対し UniProt API と / または AlphaFold DB API を呼び、``ApiResponse`` を返す。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests

from api.alphafold import AlphaFoldApiConfig, AlphafoldApiClient
from api.base import ApiResponse
from api.uniprot import UniprotApiClients
from core.http import make_session


# ------------------------------------------------------------
# データクラス
# ------------------------------------------------------------
@dataclass(frozen=True)
class AccessionApiResponses:
    """取得した API レスポンス。単独取得時は片方のみ ``None`` 以外。"""

    uniprot: Optional[ApiResponse] = None
    alphafold: Optional[ApiResponse] = None

# ------------------------------------------------------------
# 関数
# ------------------------------------------------------------
def fetch_accession_api_responses(
    accession: str,
    *,
    session: Optional[requests.Session] = None,
    include_uniprot: bool = True,
    include_alphafold: bool = True,
) -> AccessionApiResponses:
    """UniProt REST と / または AlphaFold DB の ``ApiResponse`` を取得する。

    Args:
        accession: UniProt accession
        session: HTTP セッション（複数 API で共有）
        include_uniprot: UniProt ``/uniprotkb/search`` を呼ぶか
        include_alphafold: AlphaFold ``prediction/{accession}`` を呼ぶか
    """
    if not include_uniprot and not include_alphafold:
        raise ValueError("include_uniprot と include_alphafold の少なくとも一方を True にしてください")

    sess = session or make_session()
    resp_uniprot: Optional[ApiResponse] = None
    resp_alphafold: Optional[ApiResponse] = None

    # UniProt API
    if include_uniprot:
        uniprot = UniprotApiClients(session=sess)
        resp_uniprot = uniprot.get_search_response(accession)

    if include_alphafold:
        af = AlphafoldApiClient(config=AlphaFoldApiConfig(), session=sess)
        resp_alphafold = af.get_prediction(accession)

    return AccessionApiResponses(uniprot=resp_uniprot, alphafold=resp_alphafold)


__all__ = [
    "AccessionApiResponses",
    "fetch_accession_api_responses",
]
