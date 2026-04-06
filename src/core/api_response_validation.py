# src/core/api_response_validation.py
"""ApiResponse に対する HTTP ステータス・body 形の共通バリデーション"""
from __future__ import annotations

from typing import Literal, Type

from api.base import ApiResponse

BodyKind = Literal["dict", "dict_or_list"]

_NOT_FOUND_STATUS = 404
_FETCH_ERROR_SNIPPET_LEN = 200


def validate_api_response(
    resp: ApiResponse,
    *,
    api_name: str,
    accession: str,
    not_found_exc: Type[BaseException],
    fetch_exc: Type[BaseException],
    body: BodyKind,
    append_snippet_on_fetch_error: bool = False,
) -> None:
    """HTTP と JSON body の最低限の整合性をチェックする（成功時は何も返さない）。

    メッセージは次の形式です（``api_name`` / ``accession`` 以外は固定文言）。

    - 404: ``NotFoundError: {api_name}: accession not found: {accession}``
    - 非2xx: ``FetchError: {api_name} error {status_code}``（必要時 ``raw_text`` 先頭を付与）
    - body 不適切: ``FetchError: {api_name} response has invalid body``

    Args:
        resp: ApiResponse
        api_name: API 名
        accession: UniProt accession
        not_found_exc: 404 時の例外クラス
        fetch_exc: 非2xx 時の例外クラス
        body: body の形式
        append_snippet_on_fetch_error: 非2xx 時に raw_text 先頭を付与するかどうか
    Returns:
        None
    """
    not_found_message = f"NotFoundError: {api_name}: accession not found: {accession}"

    if resp.status_code == _NOT_FOUND_STATUS:
        raise not_found_exc(not_found_message)

    if not (200 <= resp.status_code < 300):
        msg = f"FetchError: {api_name} error {resp.status_code}"
        if append_snippet_on_fetch_error and resp.raw_text:
            msg = f"{msg}: {(resp.raw_text or '')[:_FETCH_ERROR_SNIPPET_LEN]}"
        raise fetch_exc(msg)

    invalid_body_message = f"FetchError: {api_name} response has invalid body"
    b = resp.body
    if b is None:
        raise fetch_exc(invalid_body_message)
    if body == "dict" and not isinstance(b, dict):
        raise fetch_exc(invalid_body_message)
    if body == "dict_or_list" and not isinstance(b, (dict, list)):
        raise fetch_exc(invalid_body_message)
