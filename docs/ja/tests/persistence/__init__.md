# persistence テストパッケージ

> 📅 最終更新日: 2026/06/18

## 役割
`tests/persistence/` はエラー、ログ、成功結果の 3 つの永続化パス、および JSONL 解析ユーティリティ関数をカバーし、Inlet / Spout ペアコンポーネントがバックグラウンドスレッドで正しくディスクに書き込むか結果をキャッシュできることを検証します。

## 含まれるテストファイル
- `test_fail.py`: エラーレコードの JSONL 書き込み。
- `test_jsonl.py`: JSONL ファイルの解析とグループ化ユーティリティ関数。
- `test_log.py`: ログレコードのテキストファイル書き込み。
- `test_success.py`: 成功結果の `(prev_task, result)` ペアキャッシュ。

## 実行方法

```bash
pytest tests/persistence -v
pytest tests/persistence -k "fail or jsonl or log or success" -v
```
