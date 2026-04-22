# test_metrics.py テスト説明

## テスト目的

`TaskMetrics` タスクメトリクス統計クラスのすべてのカウンターロジック、重複排除メカニズム、リトライ例外設定、および状態判定を検証します。`TaskMetrics` はフレームワーク内のタスク状態の可視化と監視のデータソースであり、そのカウントの正確性は運用判断に直接影響します。

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskMetricsBasic` | 8 | 初期値、各カウンター、processed/pending の計算式、is_finished、reset |
| `TestTaskMetricsDuplicate` | 3 | 重複排除の切り替え、重複検出、reset_state のクリア |
| `TestTaskMetricsRetryExceptions` | 2 | デフォルトの空例外、動的追加 |

### 主要テストケースの詳細

#### `test_processed_equals_sum`
- **目的**：コア会計計算式を検証します：`processed = succeeded + failed + duplicated`；`pending = input - processed`。
- **入力**：10件のタスク、5件成功、2件失敗、1件重複
- **アサーション**：`processed == 8`、`pending == 2`

#### `test_is_tasks_finished_true / false`
- **目的**：`is_tasks_finished()` が `task_counter` と `success + error + duplicate` を比較して完了状態を判定することを検証します。
- **境界**：等しい場合は `True`、等しくない場合は `False` を返します。

#### `test_duplicate_check_enabled_detects_repeat`
- **目的**：重複排除を有効にした場合、同じハッシュが2回目に出現すると `True` を返すことを検証します。
- **メカニズム**：内部で `set[str]` を使用して処理済みの `task_hash` を格納します。

#### `test_duplicate_check_resets_with_reset_state`
- **目的**：`reset_state()` が `processed_set` をクリアし、以前重複排除されたタスクが再度処理可能になることを検証します。
- **注意**：`reset_counter()` はカウンター値のみをリセットし、重複排除セットはリセット**しません**。重複排除セットをリセットするには `reset_state()` が必要です。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `celestialflow.runtime.core_metrics.TaskMetrics` | テスト対象 |

## 発生しうる問題と注意事項

### 1. スレッド/プロセス安全性（現在のテストでは未カバー）
`TaskMetrics` は内部で `execution_mode` に基づいて異なるカウンター実装を選択します：
- `serial`：`ValueWrapper`（ロックなし）
- `thread`：`ValueWrapper` + `threading.Lock`
- `process`：`multiprocessing.Value`

現在の単体テストは `serial` モードでのみ実行されており、並行シナリオでのカウント競合をカバーしていません。スレッド安全性を検証するには、以下のテストを追加する必要があります：
```python
def test_thread_safe_counter():
    metrics = TaskMetrics(execution_mode="thread")
    # マルチスレッド並行 add_success_count
```

### 2. `reset_counter` と `reset_state` の責務分離
| メソッド | リセット内容 |
|---------|------------|
| `reset_counter()` | `task_counter`、`success_counter`、`error_counter`、`duplicate_counter` の値 |
| `reset_state()` | `processed_set`（重複排除セット） |

よくある誤解：`reset_counter()` を呼び出した後に重複排除セットもクリアされると期待すること。**実際にはクリアされません**。明示的に `reset_state()` を呼び出す必要があります。

### 3. `add_task_count` と `task_counter` のセマンティクス
`add_task_count(5)` は `task_counter` に初期値を累積します。`SumCounter` モードでは、この値は複数のサブカウンターの累積から得られる場合があります（`TaskSplitter` の分割カウントなど）。`task_counter.value` を直接変更すると一貫性が損なわれる可能性があります。

### 4. `is_tasks_finished` のタイミング問題
`is_tasks_finished()` はノンブロッキングの読み取り操作です。`thread` モードでは、ワーカースレッドが `add_success_count()` と `add_task_count()` の間にいる場合、一時的な中間状態が読み取られる可能性があります（`processed > input` または `processed < input`）。

**推奨事項**：staged スケジューリングモードでは、タスク実行のピーク時ではなく、レイヤー間でのみこの状態を確認してください。

### 5. リトライ例外タプルの不変性
`retry_exceptions` は `tuple[type[Exception], ...]` 型であり、`+` 演算子で拡張されます。これによりマルチスレッド読み取り時の一貫性が保証されますが、追加操作はアトミックではありません（ただし、通常は初期化段階でのみ設定されるため、現在の実装では影響しません）。

## 実行方法

```bash
pytest tests/test_metrics.py -v
```

すべてのテストケースは純粋なインメモリ操作であり、実行時間は `< 100ms` です。

## 関連ファイル

- `src/celestialflow/runtime/core_metrics.py`：テスト対象の実装
- `src/celestialflow/runtime/util_factories.py`：カウンターファクトリー（`make_counter`、`SumCounter`）
- `tests/test_executor.py`：エンドツーエンドシナリオでのメトリクスカウントの検証
