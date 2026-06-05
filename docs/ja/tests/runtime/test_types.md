# ランタイム型テスト (test_types.py)

> 📅 最終更新日: 2026/06/05

## 目的

value wrapper、sum counter、終了シグナル型、enum、永続化エラーレコードを検証します。

## 主要ポイント

- ロックあり / なし両方の `ValueWrapper` 挙動を確認します。
- frozen なエラーレコードと enum 定数を検証します。

## 実行方法

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or sum_counter" -v
pytest tests/runtime/test_types.py -k "termination or persisted_error" -v
```
