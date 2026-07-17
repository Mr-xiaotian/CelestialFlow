# タスクメトリクステスト (test_metrics.py)

> 📅 最終更新日: 2026/07/16

## 役割
`celestialflow.runtime.core_metrics` の `TaskMetrics` クラスを検証し、タスク実行中の各種統計指標（成功、失敗、重複、保留中など）が正確に計算されることを確認します。

## コアテスト対象
- `TaskMetrics`: 単一ステージ（Stage）またはグローバルのタスクカウントと状態追跡を担当します。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|-------------|---------|--------------|
| `TestTaskMetricsBasic` | 9 | 基本カウント累積、数式検証、完了判定、カウンタリセット |
| `TestTaskMetricsDuplicate` | 3 | 重複排除の有効/無効、`reset_state()` によるハッシュセットクリア |
| `TestTaskMetricsRetryExceptions` | 2 | デフォルトのリトライ可能例外が空、動的な例外型追加 |

## 主要テストシナリオ
1. **基本カウント**: `add_task_count`、`add_success_count`、`add_error_count`、`add_duplicate_count` などのメソッドの累積ロジックを検証。
2. **数式検証**: `tasks_processed = tasks_succeeded + tasks_failed + tasks_duplicated` および `tasks_pending = tasks_input - tasks_processed` を検証。
3. **状態判定**: `is_tasks_finished()` が異なるカウント組み合わせで正しい結果を返すことを検証（Pending が0の場合に True）。
4. **重複排除ロジック**:
   - 重複排除機能が無効の場合、同一ハッシュが常に `False` を返すことを検証。
   - 重複排除機能が有効の場合、同一ハッシュの2回目チェックが `True` を返すことを検証。
   - `reset_state()` がハッシュセットをクリアし、同一タスクが再度通過できることを検証。
5. **リトライ設定**: リトライ可能な例外型を動的に追加するロジックを検証。

## テストの重点
- **指標の保存則**: `tasks_input` と `tasks_processed + tasks_pending` が常に一致することを確認。
- **重複排除の正確性**: ハッシュセットが重複タスクを効果的に識別し、冗長な計算を防止することを確認。
- **リセット機能**: `reset_counter()`（数値のみリセット）と `reset_state()`（数値と重複排除セットをリセット）の違いを検証。

## 実行方法

```bash
# 全テスト実行
pytest tests/runtime/test_metrics.py -v

# 基本カウントテストのみ
pytest tests/runtime/test_metrics.py -k "count" -v

# 重複排除ロジックテストのみ
pytest tests/runtime/test_metrics.py -k "duplicate" -v

# リセット機能テストのみ
pytest tests/runtime/test_metrics.py -k "reset" -v

# リトライ設定テストのみ
pytest tests/runtime/test_metrics.py -k "retry" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestTaskMetricsBasic` / `TestTaskMetricsDuplicate` / `TestTaskMetricsRetryExceptions` | ~0.1s（純粋なロジック演算） |

## 重要な詳細
- 統計指標は Dashboard 表示とグラフ実行終了判定のデータソースです。

## 注意事項
- 統計指標の正確性は `TaskGraph` の自動クローズ判定に直接影響します。
- 関連実装は `src/celestialflow/runtime/core_metrics.py` にあります。
