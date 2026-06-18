# ログ永続化テスト (test_log.py)

> 📅 最終更新日: 2026/06/18

## 役割
`LogInlet` と `LogSpout` がグラフ起動、タスクリトライ、ノード起動などのログイベントを非同期でログファイルに書き込み、対応するレベルテキストを保持できることを検証します。

## カバレッジポイント
- `start_graph()` がグラフ起動メッセージを書き込むこと。
- `task_retry()` が例外情報付きの WARNING レベルログを書き込むこと。
- `start_stage()` がノード起動レコードを書き込むこと。

## 主要シナリオ
- 一時ディレクトリ内で `LogSpout` を起動。
- グラフ起動、タスクリトライ、ノード起動の 3 種類のログイベントを送信。
- ポーリングによりログファイルの存在を確認し、`test message`、`hello world`、`INFO`、`WARNING` などのキー内容を含むことを検証。

## 実行方法

```bash
pytest tests/persistence/test_log.py -v
pytest tests/persistence/test_log.py -k "log_persistence" -v
```
