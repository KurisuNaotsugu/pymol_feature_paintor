# src/core/paths.py
"""リポジトリの ``src`` 解決と ``sys.path`` への追加。"""
from __future__ import annotations

import sys
from pathlib import Path

SRC_NOT_FOUND_MESSAGE = (
    "pymol_feature_paintor の src が見つかりません。PyMOL をリポジトリルートで起動するか、"
    "run にはこのスクリプトの絶対パスを指定してください。"
)


def _is_project_src(candidate: Path) -> bool:
    return (candidate / "services").is_dir() and (candidate / "api").is_dir()


def resolve_project_src(
    *,
    anchor: Path | str | None = None,
    max_walk: int = 8,
) -> Path:
    """``services`` / ``api`` を含むプロジェクトの ``src`` ディレクトリを返す。

    1. まず ``Path.cwd() / "src"`` を試す（カレントがリポジトリルートのとき）。
    2. だめなら ``anchor``（スクリプトパスなど）のあるディレクトリから親を辿る。
    """
    cwd_src = Path.cwd().resolve() / "src"
    if _is_project_src(cwd_src):
        return cwd_src

    if anchor is None:
        raise RuntimeError(SRC_NOT_FOUND_MESSAGE)

    p = Path(anchor).resolve()
    here = p if p.is_dir() else p.parent
    for _ in range(max_walk):
        candidate = here / "src"
        if _is_project_src(candidate):
            return candidate
        if here.parent == here:
            break
        here = here.parent

    raise RuntimeError(SRC_NOT_FOUND_MESSAGE)


def ensure_project_src_on_syspath(
    *,
    anchor: Path | str | None = None,
) -> Path:
    """プロジェクトの ``src`` を ``sys.path`` の先頭に追加し、その ``Path`` を返す。"""
    src = resolve_project_src(anchor=anchor)
    s = str(src)
    if s not in sys.path:
        sys.path.insert(0, s)
    return src
