"""API response を受けて色付与済み ``DomainInfo`` を返すトポロジーパイプライン。"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

from api.base import ApiResponse
from services.uniprot_extractor import UniprotExtractor
from converter.constractor import DomainInfo
from converter.feature_aggregation import DomainInfoFactory, DomainInfoFactoryConfig


def domain_infos_from_response(
    resp: ApiResponse,
    *,
    accession: str,
    config: Optional[DomainInfoFactoryConfig] = None,
    extractor: Optional[UniprotExtractor] = None,
    chain: Optional[str] = None,
) -> list[DomainInfo]:
    """UniProt の API response から ``DomainInfo`` のリストを構築する。

    Args:
        resp: UniProt の API response
        accession: UniProt accession
        config: DomainInfoFactoryConfig
        extractor: UniprotExtractor
        chain: チェーン名

    Returns:
        list[DomainInfo]: ``DomainInfo`` のリスト
    """
    ext = extractor or UniprotExtractor()
    factory = DomainInfoFactory(config=config)
    features = ext.extract_features(resp, accession=accession)
    specs = factory.extract_features(features)
    if chain is not None:
        specs = [replace(s, chain=chain) for s in specs]
    return specs


__all__ = [
    "domain_infos_from_response",
]

