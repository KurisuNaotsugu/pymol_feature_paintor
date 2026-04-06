# src/converter/feature_aggregation.py
"""UniProt の feature を description ごとに集計し、DomainInfo にまとめるモジュール。"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from services.uniprot_extractor import UniprotFeatures
from converter.constractor import DomainInfo

# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _int_from_maybe_value(x: Any) -> Optional[int]:
    """UniProt API の location value の形ゆれを吸収
    
    Args:
        x: UniProt API の location value

    """
    if x is None:
        return None
    if isinstance(x, int):
        return x
    if isinstance(x, str):
        s = x.strip()
        if not s:
            return None
        if s.isdigit():
            return int(s)
        return None
    if isinstance(x, dict) and "value" in x:
        return _int_from_maybe_value(x.get("value"))
    return None


def _extract_location_segments(location: Any) -> list[tuple[int, int]]:
    """UniProt feature.location から (start,end) セグメントを抽出します。
    
    Args:
        location: UniProt API の location value

    """
    if location is None:
        return []

    if isinstance(location, list):
        segs: list[tuple[int, int]] = []
        for item in location:
            segs.extend(_extract_location_segments(item))
        return segs

    if not isinstance(location, dict):
        return []

    start = _int_from_maybe_value(location.get("start"))
    end = _int_from_maybe_value(location.get("end"))
    if start is not None and end is not None:
        return [(start, end)] if start <= end else [(end, start)]

    return []

# ------------------------------------------------------------
# クラス定義
# ------------------------------------------------------------
@dataclass
class DomainInfoFactoryConfig:
    """UniProt features から DomainInfo を作る際の設定

    Attributes:
        include_feature_types: 対象とする feature type（上位・UniProt の ``type``）のリスト。空なら全 type
        label_mode: 将来のラベル拡張用（現状は未使用）
    """
    include_feature_types: Optional[Sequence[str]] = None
    label_mode: str = "type_index"

class DomainInfoFactory:
    """``list[UniprotFeatures]`` から同一 ``description`` をまとめた DomainInfo を構築する。"""

    def __init__(self, config: Optional[DomainInfoFactoryConfig] = None):
        self.config = config or DomainInfoFactoryConfig()

    def extract_features(self, features: list[UniprotFeatures]) -> list[DomainInfo]:
        """``UniprotFeatures`` を ``description`` 単位でマージし、DomainInfo のリストにする。
        
        Args:
            features: ``UniprotFeatures`` のリスト
        """
        include = set(self.config.include_feature_types or [])
        merged: dict[str, list[tuple[int, int]]] = defaultdict(list)
        desc_to_domain_name: dict[str, str] = {}

        for feat in features:
            ftype = feat.feature
            if not ftype:
                continue
            if include and ftype not in include:
                continue
            desc = (feat.description or "").strip()
            if not desc:
                continue
            segs = _extract_location_segments(feat.location)
            for seg in segs:
                merged[desc].append(seg)
            if desc not in desc_to_domain_name:
                desc_to_domain_name[desc] = ftype

        out: list[DomainInfo] = []
        for desc in sorted(merged.keys()):
            spans = sorted(merged[desc], key=lambda t: (t[0], t[1]))
            out.append(
                DomainInfo(
                    domain_name=desc_to_domain_name[desc],
                    description=desc,
                    spans=tuple(spans),
                )
            )
        return out


__all__ = [
    "DomainInfoFactoryConfig",
    "DomainInfoFactory",
]
