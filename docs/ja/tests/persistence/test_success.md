# 成功結果キャッシュテスト (test_success.py)

> 📅 最終更新日: 2026/06/05

## 役割
`SuccessSpout` が `TaskEnvelope` から `prev` と `task` を抽出し、成功結果を `(元のタスク, 結果)` ペアとしてキャッシュし、後続のクエリで使用できることを検証します。

## カバレッジポイント
- `TaskEnvelope.prev` が元のタスク識別子として正しく保持されること。
- `SuccessSpout` のバックグラウンドスレッドがキュー内の envelope を success pair に変換すること。
- `get_success_pairs()` の戻り順序が入力と一致すること。

## 主要シナリオ
- `prev` 付きの `TaskEnvelope` を 2 つ構築。
- キュー投入後、`SuccessSpout` の消費を待機。
- 最終的に `('task1', 100)` と `('task2', 200)` の 2 つの結果が取得できることをアサート。

## 実行方法

```bash
pytest tests/persistence/test_success.py -v
pytest tests/persistence/test_success.py -k "success_persistence" -v
```
