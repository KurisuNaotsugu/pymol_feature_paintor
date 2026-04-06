# src/plugin/plugin_test.py
from __future__ import annotations

from pymol import cmd

# 実行関数の定義
def hello_pymol():
    print("Hello from plugin!")

# pymolへのコマンド登録
cmd.extend("hello_pymol", hello_pymol)
