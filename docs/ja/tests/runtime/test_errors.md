# ランタイム例外テスト (test_errors.py)

> 📅 最終更新日: 2026/06/05

## 目的

`util_errors` にある独自例外階層を検証します。

## 主要ポイント

- 継承関係、既定メッセージ、オプション系フィールドを確認します。
- 例外契約がリファクタで崩れないよう保ちます。

## 実行方法

```bash
pytest tests/runtime/test_errors.py -v
pytest tests/runtime/test_errors.py -k "invalid_option or connection" -v
```
