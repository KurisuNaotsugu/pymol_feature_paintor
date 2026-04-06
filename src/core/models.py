# src/core/models.py
"""データクラスの定義"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class StructureArtifact:
    """AlphaFold DB から取得した構造ファイルのメタ情報

    Args:
        accession(str): UniProt accession
        format(str): ファイル形式
        local_path(Path): ローカルパス
        source_url(str): ソースURL
        checksum(Optional[str]): チェックサム
    """

    accession: str
    format: str
    local_path: Path
    source_url: str
    checksum: Optional[str] = None


@dataclass(frozen=True)
class AminoAcidSequence:
    """アミノ酸配列（生の文字列 + 正規化済みの派生情報）"""

    value: str

    @property
    def normalized(self) -> str:
        """空白/改行を除去して大文字化した配列文字列。"""
        return "".join(self.value.split()).upper()

    def matches(self, other: "AminoAcidSequence") -> bool:
        """2つの配列が（正規化後に）一致するか。"""
        return self.normalized == other.normalized

