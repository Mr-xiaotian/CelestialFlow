# Base Inlet テスト (test_inlet.py)

> 📅 最終更新日: 2026/06/05

## 目的

`BaseInlet` が対象キューへ記録を投入し、実行中の `BaseSpout` 消費側がそのまま受け取れることを検証します。

## 主要ポイント

- `_funnel()` による直接キュー投入を確認します。
- 文字列と辞書のペイロードが改変されず届くことを確認します。

## 実行方法

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
