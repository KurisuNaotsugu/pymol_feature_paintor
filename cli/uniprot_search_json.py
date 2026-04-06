"""UniProt ``/uniprotkb/search`` のレスポンス body を JSON ファイルに保存する。"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap() -> None:
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "src"))
    from core.paths import ensure_project_src_on_syspath

    ensure_project_src_on_syspath(anchor=__file__)


_bootstrap()

from api.uniprot import UniprotApiClients  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="UniProt /uniprotkb/search の ApiResponse.body を JSON で保存します。",
    )
    parser.add_argument("accession", help="UniProt accession（例: P69905）")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="出力ファイル（省略時はカレントに uniprot_search_<ACCESSION>.json）",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON インデント（0 で改行なし）")
    parser.add_argument(
        "--ascii",
        action="store_true",
        help="json.dump の ensure_ascii=True（既定は False）",
    )
    args = parser.parse_args(argv)

    acc = args.accession.strip()
    if not acc:
        parser.error("accession が空です。")

    out = args.output
    if out is None:
        out = Path.cwd() / f"uniprot_search_{acc}.json"

    client = UniprotApiClients()
    written = client.save_search_response_body_json(
        acc,
        out,
        indent=args.indent,
        ensure_ascii=args.ascii,
    )
    print(written)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
