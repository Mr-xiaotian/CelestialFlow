# stage テストパッケージ

> 📅 最終更新日: 2026/08/26

## 役割
`tests/stage/` は `TaskStage`、`TaskExecutor`、および組み込み Stage コンポーネントの実行セマンティクスをカバーし、タスクの入力・出力・重複排除・終了シグナル・並行モード・ライフサイクル動作を検証します。

## 含まれるテストファイル
- `test_executor.py`: `TaskExecutor` の実行モード、リトライ、重複排除、`restore_db` 復元と設定検証。
- `test_stage.py`: `TaskStage` の基本ライフサイクルと設定検証。
- `test_stages.py`: splitter、router などの組み込み Stage コンポーネント。
- `test_dispatch.py`: `TaskDispatch` の3つのスケジューリングモード（serial/thread/async）のコア動作テスト。

## 実行方法

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
