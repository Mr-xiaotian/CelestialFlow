# stage テストパッケージ

> 📅 最終更新日: 2026/06/11

## 役割
`tests/stage/` は `TaskStage`、`TaskExecutor`、および組み込み Stage コンポーネントの実行セマンティクスをカバーし、タスクの入力・出力・重複排除・終了シグナル・並行モード・ライフサイクル動作を検証します。

## 含まれるテストファイル
- `test_executor.py`: `TaskExecutor` の実行とキュー消費。
- `test_stage.py`: `TaskStage` の基本ライフサイクルと設定検証。
- `test_stages.py`: splitter、router などの組み込み Stage コンポーネント。

## 実行方法

```bash
pytest tests/stage -v
pytest tests/stage -k "executor or stage" -v
```
