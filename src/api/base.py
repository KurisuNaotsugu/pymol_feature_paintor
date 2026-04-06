# src/api/base.py
"""APIクライアントベースクラスと関連データクラス"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import requests

from core.http import make_session


# ------------------------------------------------------------
# 例外クラス
# ------------------------------------------------------------
class FetchError(RuntimeError):
    """取得・入力に関するエラー。"""

# ------------------------------------------------------------
# データクラス
# ------------------------------------------------------------
@dataclass
class BaseApiConfig:
    """API クライアントのベースのコンフィグクラス

    Args:
        api_base: APIのベースURL
        timeout_sec: リクエストのタイムアウト時間
        max_retry: GET の最大試行回数
        delay: 再試行前の待ち秒
        retry_status: これらの HTTP ステータスのときだけ再試行
    """
    api_base: str
    timeout_sec: int = 60
    max_retry: int = 3
    delay: float = 2.0
    retry_status: frozenset[int] = frozenset({500, 502, 503, 504})

@dataclass(frozen=True)
class ApiResponse:
    """APIレスポンス格納クラス

    Args:
        status_code: HTTP ステータスコード
        headers: レスポンスヘッダ（キーは文字列）
        body: パース済み JSON（パース失敗時は None）
        raw_text: 生のレスポンス本文
    """

    status_code: int
    headers: dict[str, str]
    body: Any
    raw_text: str

# ------------------------------------------------------------
# API クライアントのベースクラス
# ------------------------------------------------------------

class BaseJsonApiClient:
    """API クライアントのベースクラス

    Attributes:
        config: API コンフィグ
        session: HTTP セッション
    """
    def __init__(self, config: BaseApiConfig, session: requests.Session | None = None):
        """初期化"""
        self.config = config
        self.session = session or make_session()

    def normalize_accession(self, accession: str) -> str:
        """アクセッションを正規化（サブクラス・サービス層から利用）。"""
        acc = accession.strip()
        if not acc:
            raise FetchError("Empty accession")
        return acc

    def _construct_url(self, endpoint: str) -> str:
        """configクラスの'api_base'と引数の'endpoint'を結合してURLを構築。

        Args:
            endpoint: エンドポイント
        """
        ep = endpoint.lstrip("/")
        return f"{self.config.api_base}/{ep}"

    def _get_response(self, url: str, *, params: Optional[dict[str, Any]] = None) -> ApiResponse:
        """GETして ApiResponse 取得
        
        Args:
            url: リクエストを送信するURL
            params: リクエストに付与するパラメータ
        """
        # GETリクエストを送信してレスポンスを取得
        r = self.session.get(url, params=params, timeout=self.config.timeout_sec)
        # bodyの取得
        body: Any = None
        try:
            if r.text.strip():
                body = r.json()
        except Exception:
            body = None
        # ヘッダーの取得
        headers = dict(r.headers) if r.headers else {}
        # ApiResponse構築
        return ApiResponse(status_code=r.status_code, headers=headers, body=body, raw_text=r.text)

    def _get_response_with_retry(self, url: str, *, params: Optional[dict[str, Any]] = None) -> ApiResponse:
        """ステータスコードが retry_status に含まれるときだけ待機して再試行する。

        Args:
            url: リクエストを送信するURL
            params: リクエストに付与するパラメータ
        """
        max_retry = self.config.max_retry
        api_response: ApiResponse | None = None
        
        for attempt in range(max_retry):
            api_response = self._get_response(url, params=params)
            if api_response.status_code not in self.config.retry_status:
                return api_response
            if attempt < max_retry - 1:
                time.sleep(self.config.delay)
        assert api_response is not None
        return api_response

    def save_response_body_json(
        self,
        response: ApiResponse,
        output_path: str | Path,
        *,
        indent: int = 2,
        ensure_ascii: bool = False,
    ) -> Path:
        """``ApiResponse.body`` を UTF-8 の JSON ファイルに書き出す。

        Args:
            response: 保存元（``body`` は JSON パース済みの dict / list 等を想定）
            output_path: 出力ファイルパス（親ディレクトリが無ければ作成する）
            indent: ``json.dump`` のインデント
            ensure_ascii: ``json.dump`` の ``ensure_ascii``

        Returns:
            書き込んだファイルの絶対パス

        Raises:
            FetchError: ``body`` が ``None`` のとき
        """
        if response.body is None:
            raise FetchError(
                f"Response body is None (HTTP {response.status_code}); cannot save as JSON."
            )
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            json.dump(response.body, f, indent=indent, ensure_ascii=ensure_ascii)
        return out.resolve()

