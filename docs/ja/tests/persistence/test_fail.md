# 失敗永続化テスト (test_fail.py)

> 📅 最終更新日: 2026/06/05

## 役割
`FailInlet` と `FailSpout` の連携時に、タスクエラーが非同期で JSONL に書き込まれ、エラー総数とメモリ内エラーペアリストが同期的に累積されることを検証します。

## カバレッジポイント
- `start_graph()` がグラフ構造コンテキストを記録すること。
- `task_error()` がタスク値と例外情報を `FailSpout` にシリアライズすること。
- `FailSpout.total_error_num` と `get_error_pairs()` が実際の処理結果を反映すること。

## 主要シナリオ
- 一時ディレクトリで spout を起動。
- `ValueError` と `RuntimeError` の 2 種類のエラーを連続して書き込み。
- バックグラウンドスレッドのディスク書き込みを待機後、JSONL ファイルが存在し、エラーレコードの数、種類、タスク値がすべて正しいことをアサート。

## 実行方法

```bash
pytest tests/persistence/test_fail.py -v
pytest tests/persistence/test_fail.py -k "fail_persistence" -v
```
