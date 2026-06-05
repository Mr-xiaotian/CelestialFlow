# persistence テストパッケージ

> 📅 最終更新日: 2026/06/05

## 目的

JSONL、ログ、失敗、成功結果の永続化テストをまとめます。

## 主要ポイント

- ファイル永続化と成功ペアのメモリ保持の両方を扱います。
- バックグラウンド spout とポーリング helper を利用します。

## 実行方法

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fail or log or success" -v
```
