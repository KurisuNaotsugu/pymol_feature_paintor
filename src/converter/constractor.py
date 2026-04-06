# src/converter/constractor.py
"""API response から取得したドメイン情報を正規化し、色付与と PyMOL 選択式構築を行う


feature_aggregation.py ドメイン情報を集計
↓
DomainInfo.build_from_spans で正規化してDomainInfoに変換
↓
DomainColorScheme.color_fill で一括色付与
↓
list[DomainInfo]を返す
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, Sequence, Tuple

from converter.color_palette import EXTRA_PYMOL_COLOR_NAMES

# ------------------------------------------------------------
# ヘルパー関数
# ------------------------------------------------------------
def _normalize_spans(spans: Sequence[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    """(start, end) のタプル列を正規化
    - 整数化
    - start<=end
    - 空禁止

    Args:
        spans: (start, end) のタプル列
    """
    normed_spans: list[tuple[int, int]] = []
    for t in spans:
        if len(t) != 2:
            raise ValueError(f"span は (start, end) の2要素タプルである必要があります: {t!r}")
        a, b = int(t[0]), int(t[1])
        if a > b:
            a, b = b, a
        normed_spans.append((a, b))
    if not normed_spans:
        raise ValueError("spans は1つ以上の区間を含む必要があります")
    return tuple(normed_spans)

# ------------------------------------------------------------
# データクラス
# ------------------------------------------------------------

@dataclass(frozen=True)
class ColorDef:
    """PyMOL に渡す色定義

    Attributes:
        name: 色名
        rgb: RGB色
    """

    name: Optional[str] = None
    rgb: Optional[Tuple[float, float, float]] = None


@dataclass(frozen=True)
class DomainInfo:
    """ドメイン情報を表すクラス

    Attributes:
        domain_name: 上位の区分（例: UniProt の feature type ``Transmembrane``）
        spans: ドメインの区間 (start, end) のタプル列
        chain: チェーン名
        color: 色定義
        description: 下位の説明（例: ``Helical`` / ``Extracellular``）。API 由来では ``domain_name`` より細かい粒度
    """

    domain_name: str
    spans: tuple[tuple[int, int], ...]
    chain: Optional[str] = None
    color: Optional[ColorDef] = None
    description: str = ""

    def __post_init__(self) -> None:
        """ドメイン名・説明の前後空白除去、spans を正規化（整数化・start<=end・空禁止）"""
        object.__setattr__(self, "domain_name", self.domain_name.strip())
        if not self.domain_name:
            raise ValueError("domain_name は空にできません")
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "spans", _normalize_spans(self.spans))

    @classmethod
    def build_from_spans(
        cls,
        domain_name: str,
        spans: Sequence[tuple[int, int]],
        *,
        chain: Optional[str] = None,
        color: Optional[ColorDef] = None,
        description: str = "",
    ) -> DomainInfo:
        """spans を正規化して DomainInfo を組み立てる。"""
        norm = _normalize_spans(spans)
        return cls(
            domain_name=domain_name,
            spans=norm,
            chain=chain,
            color=color,
            description=description,
        )


@dataclass(frozen=True)
class DomainColorScheme:
    """``list[DomainInfo]`` に対する一括着色メソッドとパレットを保持

    Attributes:
        palette: 色名の列
    """

    palette: Sequence[str] = EXTRA_PYMOL_COLOR_NAMES

    def _color_name_pool(self) -> tuple[str, ...]:
        """``palette`` を先頭から順に重複のないタプルとして返す。"""
        seen: set[str] = set()
        out: list[str] = []
        for name in self.palette:
            if name not in seen:
                seen.add(name)
                out.append(name)
        return tuple(out)

    def color_fill(self, domain_infos: list[DomainInfo]) -> list[DomainInfo]:
        """``DomainInfo`` のリストへ一括で色情報を付与

        Args:
            domain_infos: 着色対象（空リスト可）
        """

        def _has_assigned_color(c: Optional[ColorDef]) -> bool:
            """色情報が付与されているかを判定"""
            return c is not None and bool((c.name or "").strip())

        # 1. 順序を維持して color を抽出
        colors_in_order: list[Optional[ColorDef]] = [d.color for d in domain_infos]

        # 2. 色名のプールを取得
        pool = self._color_name_pool()
        used_names: set[str] = set()
        for c in colors_in_order:
            if _has_assigned_color(c):
                used_names.add((c.name or "").strip())

        available_color = [name for name in pool if name not in used_names]
        need_count = sum(1 for c in colors_in_order if not _has_assigned_color(c))
        if need_count > len(available_color):
            raise ValueError(
                f"未着色の DomainInfo が {need_count} 件ありますが、"
                f"重複しない色名はあと {len(available_color)} 個しかありません（プール {len(pool)} 色）。"
            )

        # 3. 各 DomainInfo に色名を割り当て
        it = iter(available_color)
        out: list[DomainInfo] = []
        for d, prev_color in zip(domain_infos, colors_in_order):
            if _has_assigned_color(prev_color):
                out.append(d)
                continue
            name = next(it)
            out.append(replace(d, color=ColorDef(name=name, rgb=None)))
        return out


__all__ = [
    "ColorDef",
    "DomainColorScheme",
    "DomainInfo",
]
