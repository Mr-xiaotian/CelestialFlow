# Web テスト fixture (conftest.py)

> 📅 最終更新日: 2026/06/05

## 目的

Web 層テストで共有される fixture と helper を説明します。

## 主要ポイント

- サーバーインスタンス、クライアント、一時状態の共通セットアップを提供します。
- `tests/web/*` の下支えとなる層です。

## 実行方法

```bash
pytest tests/web -v
```
