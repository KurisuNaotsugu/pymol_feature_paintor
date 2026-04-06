# src/molpaint/painter/painter.py
"""DomainInfoの各spans区間に対してPyMOLを着色するクラス"""
from __future__ import annotations

from converter.constractor import DomainInfo


class Painter:
    """``DomainInfo`` の各 ``spans`` 区間に対して PyMOL を着色するクラス。
    """

    def paint_domaininfo(
        self,
        cmd,
        object_name: str,
        domaininfo: DomainInfo,
    ) -> None:
        """単一 ``DomainInfo`` の各 spans 区間に対して PyMOL を着色する。

        Args:
            cmd: PyMOL のコマンドモジュール
            object_name: オブジェクト名
            domaininfo: 色付与済みの DomainInfo
        """
        self._validate_spec(domaininfo)

        color_def = domaininfo.color
        assert color_def is not None
        color_name = color_def.name
        assert color_name
        for selection in self._build_pymol_selections(
            object_name=object_name,
            domaininfo=domaininfo,
        ):
            cmd.color(color_name, selection)

    def _validate_spec(self, spec: DomainInfo) -> None:
        """Painter 実行前に色定義の必須項目を検証する。"""
        if spec.color is None:
            raise ValueError(
                f"color が未設定の DomainInfo があります: {spec.domain_name!r}"
            )
        if not spec.color.name:
            raise ValueError(
                f"ColorDef.name が未設定です (domain_name={spec.domain_name!r})"
            )

    def _build_pymol_selections(
        self,
        *,
        object_name: str,
        domaininfo: DomainInfo,
    ) -> list[str]:
        """domaininfo.spansから PyMOLオブジェクトの選択式を構築

        Args:
            object_name: オブジェクト名
            domaininfo: DomainInfo
        """
        out: list[str] = []
        for span in domaininfo.spans:
            start, end = int(span[0]), int(span[1])
            parts: list[str] = [object_name]
            if domaininfo.chain:
                parts.append(f"chain {domaininfo.chain}")
            if int(start) == int(end):
                parts.append(f"resi {int(start)}")
            else:
                parts.append(f"resi {int(start)}-{int(end)}")
            out.append(" and ".join(parts))
        return out
