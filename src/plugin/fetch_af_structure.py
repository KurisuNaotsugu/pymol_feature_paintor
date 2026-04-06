# src/plugin/fetch_af_structure.py
"""AlphaFold 構造取得。PyMOL はリポジトリルートをカレントにして起動するか、パッケージをインストール済みである前提。"""
from __future__ import annotations

from pymol import cmd

from api.alphafold import AlphaFoldApiConfig, AlphaFoldDBFetcherClient, AlphafoldApiClient
from api.uniprot import UniprotApiClients
from core.http import make_session
from services.alphafold_extractor import AlphaFoldDBClient
from services.sequence_validation import validate_sequence
from services.uniprot_extractor import UniprotExtractor


# 実行関数の定義
def fetch_af(acc: str):
    cli = AlphaFoldDBFetcherClient()
    art = cli.fetch_structure(acc)
    print(f"[AF] saved: {art.local_path} (from {art.source_url})")
    cmd.load(str(art.local_path), f"AF_{art.accession}")
    cmd.zoom(f"AF_{art.accession}")

    # AlphaFold DB の uniprotSequence 抽出
    session = make_session()
    accession = art.accession
    af_api = AlphafoldApiClient(config=AlphaFoldApiConfig(), session=session)
    af_api_resp = af_api.get_prediction(accession)

    print("[AF] sequence validation")
    if af_api_resp.status_code != 200:
        print(f"AlphaFold API が 200 以外を返しました: {af_api_resp.status_code}")
        return

    af_sequence = AlphaFoldDBClient().extract_uniprot_sequence_from_body(af_api_resp.body)
    if af_sequence is None:
        print("AlphaFold レスポンスに uniprotSequence/sequence が見つかりません")
        return

    # UniProt 配列を抽出（get_search_response の body を UniprotExtractor で解釈）
    uniprot_client = UniprotApiClients(session=session)
    uniprot_extractor = UniprotExtractor()
    try:
        resp_up = uniprot_client.get_search_response(accession)
        uniprot_sequence = uniprot_extractor.extract_sequence(
            resp_up, accession=accession
        )
    except Exception as e:
        print(f"UniProt API 取得失敗: {e}")
        return

    # UniProt と AlphaFold uniprotSequence の一致を検証
    result = validate_sequence(
        af_sequence=af_sequence, uniprot_sequence=uniprot_sequence
    )
    if result.match:
        print("取得した構造の配列はUniprotAPIから取得される配列と一致しています")
    else:
        print("取得した構造の配列はUniprotAPIから取得される配列と一致していません")


# pymolへのコマンド登録
cmd.extend("fetch_af", fetch_af)
