# ランタイムメトリクステスト (test_metrics.py)

> 📅 最終更新日: 2026/06/05

## 目的

executor / stage で使うカウンタ集計とメトリクススナップショットを検証します。

## 主要ポイント

- 成功・失敗・重複・待機カウンタの挙動を扱います。
- ダッシュボードやログに出る集計値の信頼性を保ちます。

## 実行方法

```bash
pytest tests/runtime/test_metrics.py -v
pytest tests/runtime/test_metrics.py -k "count or snapshot" -v
```
