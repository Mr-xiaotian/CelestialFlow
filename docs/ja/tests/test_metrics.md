# test_metrics.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

`TaskMetrics` タスクメトリクスクラスのすべてのカウンターロジック、重複排除メカニズム、リトライ例外設定、状態判定を検証します。`TaskMetrics` はフレームワーク内のタスク状態可視化とモニタリングのデータソースであり、カウンターの正確性は運用判断に直接影響します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskMetricsBasic` | 8 | 初期値、各カウンター、processed/pending 計算式、is_finished、reset |
| `TestTaskMetricsDuplicate` | 3 | 重複チェック切り替え、重複検出、reset_state クリア |
| `TestTaskMetricsRetryExceptions` | 2 | デフォルト空例外、動的追加 |

### 主要テストケースの詳細

#### `test_processed_equals_sum`
- **目的**: コア会計公式を検証：`processed = succeeded + failed + duplicated`；`pending = input - processed`。
- **入力**: 10タスク、5成功、2失敗、1重複
- **アサーション**: `processed == 8`、`pending == 2`

#### `test_is_tasks_finished_true / false`
- **目的**: `is_tasks_finished()` が `task_counter` と `success + error + duplicate` の比較で完了状態を判定することを検証。
- **境界**: 等しい場合は `True`、等しくない場合は `False` を返す。

#### `test_duplicate_check_enabled_detects_repeat`
- **目的**: 重複チェック有効時、同じハッシュが2回目に出現すると `True` を返すことを検証。
- **メカニズム**: 内部的に `set[bytes]` を使用して処理済みの `task_hash` を保存。

#### `test_duplicate_check_resets_with_reset_state`
- **目的**: `reset_state()` が `processed_set` をクリアし、以前に重複排除されたタスクが再入力可能になることを検証。
- **注意**: `reset_counter()` はカウンター値のみリセットし、重複排除セットは**リセットしません**；`reset_state()` が必要です。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_metrics.TaskMetrics` | テスト対象 |

## 起こりうる問題と注意事項

### 1. スレッド安全性（現在のテストではカバーされていない）
`TaskMetrics` は `execution_mode` に基づいて異なるカウンター実装を選択します：
- `serial`: `ValueWrapper`（ロックなし）
- `thread`: `ValueWrapper` + `threading.Lock`

現在のユニットテストは `serial` モードのみで実行されており、並行シナリオでのカウンター競合はカバーされていません。スレッド安全性を検証するには、以下のテストを追加すべきです：
```python
def test_thread_safe_counter():
    metrics = TaskMetrics(execution_mode="thread")
    # マルチスレッド並行 add_success_count
```

### 2. `reset_counter` と `reset_state` の責務分離
| メソッド | リセット内容 |
|----------|-------------|
| `reset_counter()` | `task_counter`、`success_counter`、`error_counter`、`duplicate_counter` の値 |
| `reset_state()` | `processed_set`（重複排除セット） |

よくある誤解：`reset_counter()` 呼び出し後に重複排除セットもクリアされると期待すること。**実際にはクリアされません**。`reset_state()` を明示的に呼び出す必要があります。

### 3. `add_task_count` と `task_counter` のセマンティクス
`add_task_count(5)` は `task_counter` に初期値を累積します。`SumCounter` モードでは、この値は複数のサブカウンターの累積（例: `TaskSplitter` の分割カウント）から来る場合があります。`task_counter.value` を直接変更すると一貫性が崩れる可能性があります。

### 4. `is_tasks_finished` のタイミング問題
`is_tasks_finished()` はノンブロッキングの読み取り操作です。`thread` モードでは、worker スレッドが `add_success_count()` と `add_task_count()` の間にある場合、一時的な中間状態が読み取られる可能性があります（`processed > input` または `processed < input`）。

**推奨**: staged スケジューリングモードでは、タスク実行のピーク時を避け、レイヤー間でのみこの状態をチェックしてください。

### 5. リトライ例外タプルの不変性
`retry_exceptions` は `tuple[type[Exception], ...]` 型で、`+` 演算子で追加されます。これはマルチスレッド読み取りの一貫性を保証しますが、追加操作はアトミックではありません（ただし、通常は初期化段階でのみ設定されるため、現在の実装では問題ありません）。

## 実行方法

```bash
pytest tests/test_metrics.py -v
```

すべてのテストケースは純粋なインメモリ操作であり、実行時間は `< 100ms` です。

## 関連ファイル

- `src/celestialflow/runtime/core_metrics.py`: テスト対象の実装
- `src/celestialflow/runtime/util_factories.py`: カウンターファクトリー（`make_counter`、`SumCounter`）
- `tests/test_executor.py`: エンドツーエンドシナリオでメトリクスカウントを検証
