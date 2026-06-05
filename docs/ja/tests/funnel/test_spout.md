# Base Spout テスト (test_spout.py)

> 📅 最終更新日: 2026/06/05

## 目的

spout の start/stop フック、終了処理、`_handle_record()` を実装すべき契約を検証します。

## 主要ポイント

- stop 前に投入した記録が消費されることを確認します。
- `_handle_record()` 未実装時にフレームワーク例外が発生することを確認します。

## 実行方法

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
