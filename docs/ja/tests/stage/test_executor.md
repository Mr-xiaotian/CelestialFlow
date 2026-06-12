# タスク実行者テスト (test_executor.py)

> 📅 最終更新日: 2026/06/11

## 役割
`celestialflow.stage.core_executor` の `TaskExecutor` クラスを検証し、さまざまな並行モードでタスクを正確に実行し、エラーを処理し、高度な機能（リトライや重複排除など）をサポートできることを確認します。

## コアテスト対象
- `TaskExecutor`: 単一タスクのロジックを実行する低レベルエンジン。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestExecutorSerial` | 4 | 直列実行、エラー処理、リトライ成功、非マッチ例外はリトライしない |
| `TestExecutorThread` | 1 | スレッドプール並列実行と正しいカウント |
| `TestExecutorAsync` | 2 | 非同期実行と連続処理ロジック |
| `TestExecutorDuplicateCheck` | 2 | 重複排除の有効/無効による動作比較 |
| `TestExecutorSuccessCache` | 1 | 成功結果キャッシュと `get_success_pairs()` |
| `TestExecutorConfig` | 2 | 不正な実行モードの検証、`get_summary()` サマリー情報 |

## 主要テストシナリオ

### 実行モード
- **Serial**: 順次実行。結果マッピングとカウントを検証。
- **Thread**: 並列実行。マルチスレッドでのタスク分散を検証（`execution_mode="thread"`）。
- **Async**: 非同期実行。`start_async` のコルーチン処理を検証（`execution_mode="async"`）。

### リトライ機構
- `max_retries` ロジックを検証：指定された `retry_exceptions` がスローされた場合のみリトライがトリガーされる。
- リトライ成功後、最終カウントが失敗ではなく成功としてマークされることを検証。
- 非マッチ例外（例：`RuntimeError` をリトライ設定しているが `ValueError` がスローされた）が即座に失敗をトリガーすることを検証。

### 重複排除とキャッシュ
- `enable_duplicate_check` 有効時、同一タスクは 1 回のみ実行され、重複は `tasks_duplicated` に計上されることを検証。
- `enable_duplicate_check` 無効時、同一タスクがすべて実行され、`tasks_duplicated` が 0 であることを検証。
- `get_success_pairs()` が成功したタスクの入出力ペアを正しく返すことを検証。

### 設定検証
- 不正な `execution_mode` が初期化時に `ExecutionModeError` をスローすることを検証。
- `get_summary()` が `name`、`func_name`、`execution_mode` などのキーフィールドを返すことを検証。

## テストの重点
- **実行モードの一貫性**: どの実行モードを使用しても、最終的なタスクカウントと結果収集ロジックが一貫していることを確認。
- **リトライ精度**: 非マッチ例外が即座に失敗をトリガーすることを検証。
- **並行安全性**: スレッドプールおよび非同期モードでの結果収集に競合や欠落が発生しないことを検証。

## 実行方法

```bash
# すべて実行
pytest tests/stage/test_executor.py -v

# Serial モードテストのみ実行
pytest tests/stage/test_executor.py -k "serial" -v

# Thread モードテストのみ実行
pytest tests/stage/test_executor.py -k "thread" -v

# Async モードテストのみ実行
pytest tests/stage/test_executor.py -k "async" -v

# リトライ機構テストのみ実行
pytest tests/stage/test_executor.py -k "retry" -v

# 重複排除テストのみ実行
pytest tests/stage/test_executor.py -k "duplicate" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|------|------|
| `TestExecutorSerial` | ~1s |
| `TestExecutorThread` | ~1s |
| `TestExecutorAsync` | ~2s |
| `TestExecutorDuplicateCheck` / `TestExecutorSuccessCache` / `TestExecutorConfig` | < 0.5s |

## 重要な詳細
- `flaky` クロージャを使用してリトライが必要なシナリオをシミュレート。
- `test_invalid_execution_mode` はサポートされていないモードが初期化時に即座にエラーとなることを確認。

## 注意事項
- `TaskExecutor` は `TaskStage` のコアコンポーネントであり、具体的な関数呼び出しロジックを担当。
- 関連実装は `src/celestialflow/stage/core_executor.py` にあります。
