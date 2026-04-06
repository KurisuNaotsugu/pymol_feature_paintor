# src/services/sequence_validation.py
"""AlphaFold DB の uniprotSequence と UniProt API の配列が一致するか検証する

Uniprotには様々なアイソフォームが存在するため、領域指定がずれないように配列の一致を検証する。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.models import AminoAcidSequence

# ------------------------------------------------------------
# データクラス
# ------------------------------------------------------------
@dataclass
class SequenceValidationResult:
    """配列一致検証の結果。"""

    match: bool
    af_sequence: Optional[AminoAcidSequence]
    uniprot_sequence: AminoAcidSequence
    message: str

# ------------------------------------------------------------
# 関数
# ------------------------------------------------------------
def validate_sequence(af_sequence: AminoAcidSequence, uniprot_sequence: AminoAcidSequence) -> SequenceValidationResult:
    """抽出済みの配列同士を比較し、一致するかを判定

    Args:
        af_sequence: AlphaFold のアミノ酸配列
        uniprot_sequence: UniProt のアミノ酸配列
    Returns:
        SequenceValidationResult: 配列一致検証の結果
    """
    match = af_sequence.matches(uniprot_sequence)

    if match:
        msg = f"一致しました（長さ: {len(af_sequence.normalized)} aa）"
    else:
        msg = (
            f"不一致: AF長={len(af_sequence.normalized)}, "
            f"UniProt長={len(uniprot_sequence.normalized)}"
        )

    return SequenceValidationResult(
        match=match,
        af_sequence=af_sequence,
        uniprot_sequence=uniprot_sequence,
        message=msg,
    )

__all__ = [
    "SequenceValidationResult",
    "validate_sequence",
]
