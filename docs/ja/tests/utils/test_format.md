# 整形 utility テスト (test_format.py)

> 📅 最終更新日: 2026/06/05

## 目的

表形式出力や人間向け表示など、整形 helper の挙動を検証します。

## 主要ポイント

- コンソール向け出力が安定していることを確認します。
- docs や CLI 例で使う表示 helper を保護します。

## 実行方法

```bash
pytest tests/utils/test_format.py -v
pytest tests/utils/test_format.py -k "table or format" -v
```
