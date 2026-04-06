#!/usr/bin/env python3
"""UniProt API → UniprotExtractor / DomainInfoFactory → DomainColorScheme を確認する統合テスト。

使い方:
  python tests/test_feature_extract.py Q1EHB4
  python tests/test_feature_extract.py Q1EHB4 --feature-types Transmembrane
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))

from core.paths import ensure_project_src_on_syspath  # noqa: E402

ensure_project_src_on_syspath(anchor=__file__)

from api.uniprot import UniprotApiClients  # noqa: E402
from core.http import make_session  # noqa: E402
from converter.constractor import DomainColorScheme, DomainInfo  # noqa: E402
from converter.feature_aggregation import DomainInfoFactoryConfig  # noqa: E402
from converter.pipeline import domain_infos_from_response  # noqa: E402

# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _fmt_spans(spec: DomainInfo) -> str:
    """(start, end) のタプル列を "start-end" の形式で連結した文字列を返す。"""
    return ", ".join(f"{a}-{b}" for a, b in spec.spans)


def _fmt_color(spec: DomainInfo) -> str:
    """着色後の PyMOL 色名（未設定なら "-"）。"""
    if spec.color is None or not (spec.color.name or "").strip():
        return "-"
    return spec.color.name.strip()


def _print_specs(specs: Iterable[DomainInfo]) -> None:
    """DomainInfo のリストを全件表示する。"""
    spec_list = list(specs)
    print(f"DomainInfo count: {len(spec_list)}")
    if not spec_list:
        raise ValueError("抽出条件に一致する feature がありません。")
    for i, spec in enumerate(spec_list, start=1):
        print(
            f"  [{i:02d}] {spec.domain_name:18s} {spec.description:16s} "
            f"color={_fmt_color(spec):12s} spans={_fmt_spans(spec)}"
        )

# ------------------------------------------------------------
# メイン関数
# ------------------------------------------------------------
def main() -> int:
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="UniProt API から取得した features を factory で DomainInfo に変換し色付与するテスト",
    )
    parser.add_argument("accession", help="UniProt accession（例: Q1EHB4）")
    parser.add_argument(
        "--feature-types",
        nargs="*",
        default=None,
        dest="feature_types",
        help="含める feature type を指定（未指定なら全 type）",
    )
    parser.add_argument(
        "--label-mode",
        choices=("type", "type_index"),
        default="type_index",
        help="factory のラベル作成モード（既定: type_index）",
    )
    args = parser.parse_args()

    # initialize
    accession = args.accession.strip()
    session = make_session()
    uniprot = UniprotApiClients(session=session)
    config = DomainInfoFactoryConfig(
        include_feature_types=args.feature_types,
        label_mode=args.label_mode,
    )

    # UniProt API から features を取得
    print("=" * 72)
    print("1) UniProt API から features を取得（UniprotApiClients → converter.pipeline）")
    print("=" * 72)
    print(f"accession: {accession}")
    print(f"feature_types filter: {args.feature_types if args.feature_types else '(all)'}")
    print(f"label_mode: {args.label_mode}")

    try:
        resp = uniprot.get_search_response(accession)
        specs = None
        if 200 <= resp.status_code < 300:
            specs = DomainColorScheme().color_fill(
                domain_infos_from_response(
                    resp,
                    accession=accession,
                    config=config,
                )
            )
    except Exception as e:
        print(f"[ERROR] UniProt 取得または features 抽出に失敗: {e}")
        return 1

    print(f"UniProt status_code: {resp.status_code}")
    if not (200 <= resp.status_code < 300):
        raw_snippet = (resp.raw_text or "")[:500].replace("\n", "\\n")
        print(f"UniProt raw_text (snippet): {raw_snippet}")
        if isinstance(resp.body, dict):
            print(f"UniProt body keys: {list(resp.body.keys())}")
        return 1

    assert specs is not None
    print(f"features -> DomainInfo（色付与済み）件数: {len(specs)}")
    print("\n" + "=" * 72)
    print("2) DomainInfo 一覧（DomainColorScheme.color_fill 適用後）")
    print("=" * 72)

    try:
        _print_specs(specs)
    except Exception as e:
        print(f"[ERROR] 表示に失敗: {e}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
