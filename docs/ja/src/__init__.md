# CelestialFlow パッケージ入口

> 📅 最終更新日: 2026/06/05

## 目的

`celestialflow.__init__` から公開されるパッケージレベル API をまとめ、どの graph、stage、web、persistence、utility シンボルを直接 import すべきかを示します。

## 主要ポイント

- graph、stage、observability、utils、web、persistence、runtime の主要エクスポート群を要約します。
- `from celestialflow import ...` が高水準の基本 import 経路であることを説明します。
- パッケージ公開シンボルの索引ページとして機能します。
