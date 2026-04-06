#!/usr/bin/env python3
"""AlphaFold / UniProt API の統合確認（ネットワーク必須・pytest 不使用）。

手順:
  1. ``api.pipeline.fetch_accession_api_responses`` で UniProt と AlphaFold の ``ApiResponse`` を取得
  2. ``services.alphafold_extractor.AlphaFoldDBClient`` で構造 URL と AF 側配列を抽出
  3. ``services.uniprot_extractor.UniprotExtractor`` で UniProt 配列を抽出
  4. ``services.sequence_validation.validate_sequence`` で一致を確認
  5. ``api.alphafold.AlphaFoldDBFetcherClient.check_structure_url_reachable`` で URL が応答するか確認

実行例::

  python tests/test_alphafold_api.py P69905
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root / "src"))

from core.paths import ensure_project_src_on_syspath  # noqa: E402

ensure_project_src_on_syspath(anchor=__file__)

from api.alphafold import AlphaFoldDBFetcherClient  # noqa: E402
from api.pipeline import fetch_accession_api_responses  # noqa: E402
from core.http import make_session  # noqa: E402
from services.alphafold_extractor import AlphaFoldDBClient  # noqa: E402
from services.sequence_validation import validate_sequence  # noqa: E402
from services.uniprot_extractor import UniprotExtractor  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="UniProt + AlphaFold API の取得・配列一致・構造 URL 応答を確認する",
    )
    parser.add_argument(
        "accession",
        nargs="?",
        default="P69905",
        help="UniProt accession（既定: P69905）",
    )
    args = parser.parse_args()
    accession = (args.accession or "").strip()

    if not accession:
        print("[ERROR] accession が空です", file=sys.stderr)
        return 1

    session = make_session()

    # 1) UniProt + AlphaFold API
    print("1) fetch_accession_api_responses ...")
    bundle = fetch_accession_api_responses(accession, session=session)
    if bundle.uniprot is None or bundle.alphafold is None:
        print("[ERROR] UniProt または AlphaFold の ApiResponse がありません", file=sys.stderr)
        return 1
    if not (200 <= bundle.uniprot.status_code < 300):
        print(f"[ERROR] UniProt HTTP {bundle.uniprot.status_code}", file=sys.stderr)
        return 1
    if not (200 <= bundle.alphafold.status_code < 300):
        print(f"[ERROR] AlphaFold HTTP {bundle.alphafold.status_code}", file=sys.stderr)
        return 1
    print(f"   UniProt={bundle.uniprot.status_code}, AlphaFold={bundle.alphafold.status_code}")

    # 2) 構造 URL + AlphaFold 配列
    print("2) AlphaFoldDBClient: 構造 URL / 配列 ...")
    af_parser = AlphaFoldDBClient()
    try:
        struct_url, fmt = af_parser.pick_structure_url(bundle.alphafold, accession)
    except Exception as e:
        print(f"[ERROR] pick_structure_url: {e}", file=sys.stderr)
        return 1
    if not struct_url.startswith("http"):
        print("[ERROR] 構造 URL が http(s) ではありません", file=sys.stderr)
        return 1
    if fmt not in af_parser.FORMAT_TO_EXTENSION:
        print(f"[ERROR] 想定外の format: {fmt}", file=sys.stderr)
        return 1

    af_sequence = af_parser.extract_uniprot_sequence_from_body(bundle.alphafold.body)
    if af_sequence is None:
        print("[ERROR] AlphaFold に uniprotSequence/sequence がありません", file=sys.stderr)
        return 1
    print(f"   structure_url={struct_url!r}, format={fmt}")

    # 3) UniProt 配列
    print("3) UniprotExtractor: 配列 ...")
    try:
        uni = UniprotExtractor()
        uniprot_sequence = uni.extract_sequence(bundle.uniprot, accession=accession)
    except Exception as e:
        print(f"[ERROR] extract_sequence: {e}", file=sys.stderr)
        return 1

    # 4) 配列一致
    print("4) validate_sequence ...")
    result = validate_sequence(af_sequence, uniprot_sequence)
    print(f"   {result.message}")
    if not result.match:
        return 1

    # 5) 構造 URL 応答
    print("5) AlphaFoldDBFetcherClient.check_structure_url_reachable ...")
    fetcher = AlphaFoldDBFetcherClient(session=session)
    if not fetcher.check_structure_url_reachable(struct_url):
        print(f"[ERROR] 構造 URL が応答しません: {struct_url}", file=sys.stderr)
        return 1
    print("   OK")

    print("すべて成功しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
