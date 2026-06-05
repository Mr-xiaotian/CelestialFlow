# 成功ペアテスト (test_success.py)

> 📅 最終更新日: 2026/06/05

## 目的

`SuccessSpout` が処理済み envelope から `(元タスク, 結果)` ペアを取り出すことを検証します。

## 主要ポイント

- `prev` による元タスク追跡を確認します。
- ペア順序がキュー消費順と一致することを確認します。

## 実行方法

```bash
pytest tests/persistence/test_success.py -v
pytest tests/persistence/test_success.py -k "success_persistence" -v
```
