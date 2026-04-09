# src/converter/csv_loader.py
"""CSV から ``list[DomainInfo]`` を構築する。

想定する CSV（1 行につき 1 区間）:

- 許容される列名は ``domain_name``, ``description``, ``start``, ``end``, ``chain``, ``color`` のみ
  （大文字・小文字は区別しない）。上記以外の列名があるとエラーとする。
- 必須となる値: 各行について ``domain_name``, ``start``, ``end``
- 省略可能: ``description``（無い場合は空文字）、``chain``, ``color``

同一の ``(domain_name, description, chain)`` に属する複数行は、1 つの ``DomainInfo`` にまとめ、
``spans`` は開始位置順に並べる。
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import IO, Optional, Union

from converter.constractor import ColorDef, DomainInfo

_ALLOWED_COLUMNS = frozenset(
    ("domain_name", "description", "start", "end", "chain", "color")
)


def _validate_csv_headers(fieldnames: Optional[list[str]]) -> None:
    if not fieldnames:
        return
    invalid = [
        name
        for name in fieldnames
        if name is not None and name.strip() and name.strip().lower() not in _ALLOWED_COLUMNS
    ]
    if invalid:
        allowed = ", ".join(sorted(_ALLOWED_COLUMNS))
        bad = ", ".join(repr(x) for x in invalid)
        raise ValueError(
            f"許容されない列名があります: {bad}。許容される列名は次のみです: {allowed}"
        )


def _row_to_canonical(raw: dict[str, str]) -> dict[str, str]:
    out: dict[str, str] = {k: "" for k in _ALLOWED_COLUMNS}
    for k, v in raw.items():
        if k is None:
            continue
        key = k.strip().lower()
        if key in _ALLOWED_COLUMNS:
            out[key] = (v or "").strip()
    return out

# ------------------------------------------------------------
# メイン関数
# ------------------------------------------------------------
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

    _validate_csv_headers(reader.fieldnames)

    groups: dict[tuple[str, str, Optional[str]], list[tuple[int, int]]] = defaultdict(list)
    first_color: dict[tuple[str, str, Optional[str]], str] = {}

    for lineno, raw in enumerate(reader, start=2):
        row = _row_to_canonical(raw)
        if not any(row.values()):
            continue
        domain = row["domain_name"]
        description = row["description"]
        start_s = row["start"]
        end_s = row["end"]
        if not domain or not start_s or not end_s:
            raise ValueError(
                f"行 {lineno}: domain_name, start, end が必要です"
            )
        try:
            start, end = int(start_s), int(end_s)
        except ValueError as exc:
            raise ValueError(
                f"行 {lineno}: start と end は整数である必要があります: {exc}"
            ) from exc

        chain_raw = row["chain"]
        chain: Optional[str] = chain_raw if chain_raw else None
        key = (domain, description, chain)
        groups[key].append((start, end))

        color_raw = row["color"]
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

# ------------------------------------------------------------
# モジュール公開関数
# ------------------------------------------------------------
__all__ = [
    "load_domain_infos_from_csv",
    "load_domain_infos_from_csv_file",
]
