# utils テストパッケージ

> 📅 最終更新日: 2026/06/11

## 役割
`tests/utils/` は CelestialFlow の汎用ユーティリティ関数をカバーし、グラフ構造のクローンと端末フォーマット出力を含みます。

## 含まれるテストファイル
- `test_clone.py`: `clone_executor`、`clone_stage`、`clone_graph` のディープコピーと独立性を検証。
- `test_format.py`: `format_repr`（文字列の短縮とエスケープ）と `format_table`（端末テーブルレンダリング）を検証。

## 実行方法

```bash
pytest tests/utils -v
pytest tests/utils -k "clone or format" -v
```
