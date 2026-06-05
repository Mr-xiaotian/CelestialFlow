# 失敗永続化テスト (test_fail.py)

> 📅 最終更新日: 2026/06/05

## 目的

`FailInlet` と `FailSpout` がエラー記録を JSONL に保存し、メモリ上のエラーペアも維持することを検証します。

## 主要ポイント

- 総エラー数の加算を確認します。
- タスク値とエラー型がシリアライズ後も保たれることを確認します。

## 実行方法

```bash
pytest tests/persistence/test_fail.py -v
pytest tests/persistence/test_fail.py -k "fail_persistence" -v
```
