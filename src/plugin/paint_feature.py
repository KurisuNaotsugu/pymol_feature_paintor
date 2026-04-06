# src/plugin/paint_feature.py
"""UniProt feature の登録・着色および登録したオブジェクトの一覧表示・詳細表示"""
from __future__ import annotations

from typing import Dict, List

from pymol import cmd

from api.uniprot import UniprotApiClients
from molpaint.painter import Painter
from converter.constractor import DomainColorScheme, DomainInfo
from converter.csv_loader import load_domain_infos_from_csv
from converter.pipeline import domain_infos_from_response
from converter.feature_aggregation import DomainInfoFactoryConfig

# ------------------------------------------------------------
# 登録状態　{変数名 : List[DomainInfo]}
# ------------------------------------------------------------
_registry: Dict[str, List[DomainInfo]] = {}

# preview_feature_domains_from_accession の結果（register_feature_domain_subset が参照）
_preview_infos: List[DomainInfo] | None = None
_preview_accession: str = ""

# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _norm_registry_name(name: str) -> str:
    n = name.strip()
    if not n:
        raise ValueError("registry name must not be empty")
    return n


def _merge_into_registry(name: str, infos: List[DomainInfo]) -> None:
    """同名が既にあれば ``DomainInfo`` 列を後ろに結合する。"""
    key = _norm_registry_name(name)
    prev = _registry.get(key, [])
    _registry[key] = prev + infos


def _format_domain_info(d: DomainInfo, index: int) -> str:
    """閲覧用に 1 件の DomainInfo を整形する。"""
    lines = [
        f"  --- [{index}] ---",
        f"  domain_name: {d.domain_name!r}",
        f"  description: {d.description!r}",
        f"  spans:       {list(d.spans)}",
    ]
    if d.chain is not None and str(d.chain).strip():
        lines.append(f"  chain:       {d.chain!r}")
    if d.color is not None:
        cn = (d.color.name or "").strip() or None
        rgb = d.color.rgb
        if cn:
            lines.append(f"  color.name:  {cn!r}")
        if rgb is not None:
            lines.append(f"  color.rgb:   {rgb}")
        if cn is None and rgb is None:
            lines.append("  color:       (未設定)")
    else:
        lines.append("  color:       (未設定)")
    return "\n".join(lines)

# ------------------------------------------------------------
# 登録関数（UniProt accession）
# ------------------------------------------------------------
def preview_feature_domains_from_accession(
    accession: str,
    chain: str = "",
    label_mode: str = "type_index",
) -> None:
    """UniProt API から全 feature type を対象に ``List[DomainInfo]`` を構築し、
    ``domain_name`` / ``description`` の一覧を表示する。結果は次の ``register_feature_domain_subset`` 用に保持する。

    Args:
        accession: UniProt accession
        chain: チェーン（省略可）
        label_mode: ``DomainInfoFactoryConfig.label_mode``
    """
    global _preview_infos, _preview_accession

    acc = accession.strip()
    if not acc:
        raise ValueError("accession must not be empty")
    chain_arg = chain.strip() or None
    up = UniprotApiClients()
    resp = up.get_search_response(acc)
    infos = domain_infos_from_response(
        resp,
        accession=acc,
        config=DomainInfoFactoryConfig(
            include_feature_types=None,
            label_mode=label_mode,
        ),
        chain=chain_arg,
    )
    _preview_infos = infos
    _preview_accession = acc

    print(f"[feature preview] accession={acc!r}  DomainInfo {len(infos)} 件（全 feature type）")
    for i, d in enumerate(infos, 1):
        print(f"  [{i:4d}]  domain_name={d.domain_name!r}  description={d.description!r}")
    print("[feature preview] 上記を元に register_feature_domain_subset で登録できます。")


def register_feature_domain_subset(
    registry_name: str,
    domain_name: str = "",
    description: str = "",
) -> None:
    """直前の ``preview_feature_domains_from_accession`` で保持した ``List[DomainInfo]`` から、
    ``domain_name`` / ``description`` で絞り込み（両方指定時は AND）、レジストリに結合登録する。

    Args:
        registry_name: レジストリキー
        domain_name: 絞り込み（完全一致・空なら条件に含めない）
        description: 絞り込み（完全一致・空なら条件に含めない）
    """
    if _preview_infos is None:
        raise RuntimeError(
            "先に preview_feature_domains_from_accession を実行してください。"
        )
    want_dn = domain_name.strip()
    want_ds = description.strip()
    if not want_dn and not want_ds:
        raise ValueError(
            "domain_name と description の少なくとも一方を指定してください。"
        )

    filtered: list[DomainInfo] = []
    for d in _preview_infos:
        if want_dn and d.domain_name != want_dn:
            continue
        if want_ds and d.description != want_ds:
            continue
        filtered.append(d)

    if not filtered:
        raise RuntimeError(
            f"条件に一致する DomainInfo がありません（accession={_preview_accession!r}, "
            f"domain_name={want_dn!r}, description={want_ds!r}）。"
        )

    _merge_into_registry(registry_name, filtered)
    key = _norm_registry_name(registry_name)
    print(
        f"[feature registry] 登録しました: {key!r} に {len(filtered)} 件の DomainInfo を追加 "
        f"（このキー合計 {len(_registry[key])} 件）"
    )


def register_feature_from_csv(
    registry_name: str,
    csv_path: str,
    encoding: str = "utf-8",
) -> None:
    """CSV から ``List[DomainInfo]`` を構築し、``registry_name`` に結合登録

    Args:
        registry_name: pymol オブジェクト名
        csv_path: CSV ファイルパス
        encoding: CSV ファイルエンコーディング
    """
    path = (csv_path or "").strip()
    if not path:
        raise ValueError("csv_path must not be empty")
    enc = (encoding or "").strip() or "utf-8"
    infos = load_domain_infos_from_csv(path, encoding=enc)
    _merge_into_registry(registry_name, infos)
    key = _norm_registry_name(registry_name)
    print(
        f"[feature registry] 登録しました: {key!r} に {len(infos)} 件の DomainInfo を追加 "
        f"（このキー合計 {len(_registry[key])} 件）"
    )
# ------------------------------------------------------------
# 着色関数
# ------------------------------------------------------------

def paint_feature(
    registry_name: str,
    object_name: str = "",
) -> None:
    """登録済み ``DomainInfo`` を ``color_fill`` し PyMOL オブジェクトに塗る。

    着色後の ``DomainInfo``（``ColorDef`` 付き）でレジストリを置き換えるため、
    ``show_feature_domain_infos`` でも色名が参照できる。

    Args:
        registry_name: 登録名
        object_name: 着色対象の PyMOL オブジェクト名
    """
    key = _norm_registry_name(registry_name)
    domain_infos = _registry.get(key)
    if not domain_infos:
        raise RuntimeError(
            f"登録名 {key!r} に DomainInfo がありません。"
        )

    obj = object_name.strip()
    if not obj:
        raise ValueError(
            "object_name を指定してください。構造は事前に load してから paint_feature を実行してください。"
        )

    if obj not in cmd.get_object_list():
        raise RuntimeError(
            f"オブジェクト {obj!r} が未ロードです。"
            "fetch_af などで構造を load してから paint_feature を実行してください。"
        )

    fill = DomainColorScheme()
    colored = fill.color_fill(domain_infos)
    _registry[key] = colored
    painter = Painter()
    for region in colored:
        painter.paint_domaininfo(cmd, obj, region)


# ------------------------------------------------------------
# 一覧表示・詳細表示関数
# ------------------------------------------------------------

def list_feature_registry() -> None:
    """登録済みのレジストリ名（オブジェクト名に使った登録キー）と DomainInfo 件数を表示する。"""
    if not _registry:
        print("[feature registry] 登録はありません。")
        return
    for name in sorted(_registry.keys()):
        n = len(_registry[name])
        print(f"  {name!r}  ({n} 件)")
    print(f"[feature registry] 登録名 {len(_registry)} 件")


def show_feature_domain_infos(registry_name: str) -> None:
    """指定した登録名に結合されている DomainInfo を一覧表示する。

    Args:
        registry_name: ``register_feature_*`` で使った登録名（レジストリキー）
    """
    key = _norm_registry_name(registry_name)
    if key not in _registry:
        raise RuntimeError(
            f"登録名 {key!r} はありません。list_feature_registry で一覧を確認してください。"
        )
    infos = _registry[key]
    if not infos:
        print(f"[feature registry] {key!r} の DomainInfo は 0 件です。")
        return
    print(f"[feature registry] {key!r} の DomainInfo（{len(infos)} 件）")
    for i, d in enumerate(infos, 1):
        print(_format_domain_info(d, i))


cmd.extend("preview_feature_domains_from_accession", preview_feature_domains_from_accession)
cmd.extend("register_feature_domain_subset", register_feature_domain_subset)
cmd.extend("register_feature_from_csv", register_feature_from_csv)
cmd.extend("paint_feature", paint_feature)
cmd.extend("list_feature_registry", list_feature_registry)
cmd.extend("show_feature_domain_infos", show_feature_domain_infos)
