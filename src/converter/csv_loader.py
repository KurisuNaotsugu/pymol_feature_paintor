"""CSV から ``list[DomainInfo]`` を構築する。

想定する CSV（1 行につき 1 区間）:

- 必須列: ドメイン名・開始・終了（列名はエイリアス可、下記）
- 任意列: チェーン ID、PyMOL 色名

同一の ``(domain_name, description, chain)`` に属する複数行は、1 つの ``DomainInfo`` にまとめ、
``spans`` は開始位置順に並べる。``description`` 列が無い場合は空文字として扱う。
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import IO, Optional, Union

from converter.constractor import ColorDef, DomainInfo

_FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "domain_name": ("domain_name", "domain", "name", "feature_type", "type", "feature"),
    "description": ("description", "desc", "detail"),
    "start": ("start", "begin", "from"),
    "end": ("end", "stop", "to"),
    "chain": ("chain", "chain_id"),
    "color": ("color", "color_name", "pymol_color"),
}


def _norm_row(raw: dict[str, str]) -> dict[str, str]:
    return {k.strip().lower(): (v or "").strip() for k, v in raw.items()}


def _field(norm: dict[str, str], canonical: str) -> str:
    for alias in _FIELD_ALIASES.get(canonical, (canonical,)):
        if alias in norm:
            return norm[alias]
    return ""


def load_domain_infos_from_csv_file(f: IO[str]) -> list[DomainInfo]:
    """テキストストリーム（CSV）から ``DomainInfo`` のリストを構築する。

    Args:
        f: ``newline=""`` で開いたテキストストリームを推奨（``csv`` モジュールの慣例）

    Returns:
        マージ・ソート済みの ``DomainInfo`` のリスト（空 CSV は ``[]``）
    """
    reader = csv.DictReader(f)
    if not reader.fieldnames:
        return []

    groups: dict[tuple[str, str, Optional[str]], list[tuple[int, int]]] = defaultdict(list)
    first_color: dict[tuple[str, str, Optional[str]], str] = {}

    for lineno, raw in enumerate(reader, start=2):
        norm = _norm_row(raw)
        if not any(norm.values()):
            continue
        domain = _field(norm, "domain_name")
        description = _field(norm, "description")
        start_s = _field(norm, "start")
        end_s = _field(norm, "end")
        if not domain or not start_s or not end_s:
            raise ValueError(
                f"行 {lineno}: domain_name（または domain / name 等）, start, end が必要です"
            )
        try:
            start, end = int(start_s), int(end_s)
        except ValueError as exc:
            raise ValueError(
                f"行 {lineno}: start と end は整数である必要があります: {exc}"
            ) from exc

        chain_raw = _field(norm, "chain")
        chain: Optional[str] = chain_raw if chain_raw else None
        key = (domain, description, chain)
        groups[key].append((start, end))

        color_raw = _field(norm, "color")
        if color_raw and key not in first_color:
            first_color[key] = color_raw

    out: list[DomainInfo] = []
    for key in sorted(groups.keys(), key=lambda k: (k[0], k[1], k[2] or "")):
        domain, description, chain = key
        spans = sorted(groups[key], key=lambda t: (t[0], t[1]))
        cname = first_color.get(key)
        color: Optional[ColorDef] = ColorDef(name=cname, rgb=None) if cname else None
        out.append(
            DomainInfo.build_from_spans(
                domain,
                spans,
                chain=chain,
                color=color,
                description=description,
            )
        )
    return out


def load_domain_infos_from_csv(
    path: Union[str, Path],
    *,
    encoding: str = "utf-8",
) -> list[DomainInfo]:
    """CSV ファイルから ``DomainInfo`` のリストを構築する。

    Args:
        path: CSV ファイルパス
        encoding: ファイルエンコーディング

    Returns:
        ``load_domain_infos_from_csv_file`` と同じ規則のリスト
    """
    p = Path(path)
    with p.open(encoding=encoding, newline="") as f:
        return load_domain_infos_from_csv_file(f)


__all__ = [
    "load_domain_infos_from_csv",
    "load_domain_infos_from_csv_file",
]
