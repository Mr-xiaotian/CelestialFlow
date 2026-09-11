# 具象ノードクラステスト (test_nodes.py)

> 📅 最終更新日: 2026/09/10

## 役割

`celestialflow.node.core_nodes` 内の 3 つの具象ノードクラス `TaskExecutor` / `TaskSplitter` / `TaskRouter` の実行・分割・ルーティング挙動を検証します。直列 / スレッド / 非同期の 3 つの実行モード、重複チェックデフォルト値の Web 互換性、sqlite からの永続化リプレイ、ノード初期化制約、ルーティングカウンタの安定ロックをカバーします。

## コアテスト対象

| クラス / 関数 | 役割 | 説明 |
|-----------|------|------|
| `TaskExecutor` | 被テスト対象 | 汎用エグゼキュータ。`serial` / `thread` / `async`、例外処理、retry、duplicate、`restore_db` を検証 |
| `TaskSplitter` | 被テスト対象 | 1→N スプリッタ。`split_counter`、空イテラブル、ジェネレータ、カスタム `split_item` を検証 |
| `TaskRouter` | 被テスト対象 | ルータ。`route_counters`、未知 target で `InvalidOptionError`、安定ロックを検証 |
| `append_records` | ユーティリティ | `celestialflow.persistence.util_sqlite` を介して failed / pending レコードを直接書き込み、リプレイテストに使用 |
| `build_result_dict` | ユーティリティ | `get_success_pairs` と `get_error_pairs` を集約して `{task: result_or_error_str}` を構築 |

## 主要テストシナリオ

### `TestTaskExecutor` — エグゼキュータ（17 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_serial_basic` | 直列実行 5 タスク、succeeded=5、failed=0、pending=0 |
| `test_serial_with_errors` | 直列実行 `[1,-1,2,-2,3]`、`PersistedError.error_type == "ValueError"`、succeeded=3 / failed=2 |
| `test_serial_retry` | `RuntimeError` をリトライ可能として登録；最初の 2 回失敗後、3 回目で `x+100` を返却、`call_count == 3` |
| `test_serial_no_retry_for_unmatched_exception` | 未登録のリトライ可能例外はリトライをトリガせず、直接 failed になる |
| `test_thread_basic` | スレッドモード（4 worker）で 5 タスクを正常処理 |
| `test_async_basic` | 非同期モードで 3 タスクを正常処理 |
| `test_async_double` | 非同期モードで 20 タスクを連続処理 |
| `test_duplicate_check_disabled_by_default` | **回帰**：`enable_duplicate_check` のデフォルトが `False`、重複タスクはカウントされない |
| `test_duplicate_check_enabled` | 明示的に有効化時、succeeded=3 / duplicated=3 |
| `test_duplicate_check_disabled` | 明示的に無効化時、succeeded=6 / duplicated=0 |
| `test_restore_db` | デフォルトでは自ノード `stage == self.get_name()` の failed / pending のみ読み取り、3 件の成功をリプレイ |
| `test_restore_db_filters_error_type_when_enabled` | `filter_by_error_type=True` + `set_retry_exceptions(RuntimeError)` 時、RuntimeError のみリプレイ |
| `test_restore_db_filter_keeps_pending_records` | フィルタ有効時でも `pending` レコードは常に保持される |
| `test_success_persist` | 成功結果が `LifecycleSpout` キャッシュに書き込まれ、`get_success_pairs()` から読み戻せる |
| `test_rejects_zero_argument_func` | 0 引数関数は `ConfigurationError` を送出する |
| `test_rejects_multi_argument_func` | 多引数関数は `ConfigurationError` を送出する |
| `test_name_and_execution_mode` | `get_name()` と `execution_mode` が正しく公開される |

### `TestTaskSplitter` — スプリッタ（5 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_splitter_init` | デフォルト `execution_mode="serial"`、`max_retries=0`、`split_counter.get() == 0` |
| `test_splitter_process_success` | `TaskGraph` 直列接続後の下流 `tasks_succeeded == 3`、`split_counter == 3` |
| `test_splitter_allows_empty_iterable` | 空イテラブルは例外を投げず、下流 succeeded=0、split_counter=0 |
| `test_splitter_supports_generator_input` | 一度きりジェネレータも完全に分割される（split_counter=3） |
| `test_splitter_allows_constructor_split_item` | コンストラクタ引数 `split_item=lambda item: item.strip()` で `_split([" a ", " b ", " c "]) == ("a", "b", "c")` |

### `TestTaskRouter` — ルータ（4 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_router_init` | デフォルト `serial` / `max_retries=0` / `route_counters == {}` |
| `test_router_route_logic` | `_route` が `(target, task)` を返す；未登録 target で `InvalidOptionError` |
| `test_router_process_success` | `TaskGraph` 内の 2 つの下流 `target1` / `target2` がそれぞれ 1 件ずつ受信、`route_counters` もそれぞれ = 1 |
| `test_router_binding_counter_uses_stable_metrics_lock` | ルーティングカウンタは生成時から `metrics.lock` にバインドされ、`execution_mode` を切り替えてもロックオブジェクトは変化しない |

## 主要データフロー

```mermaid
flowchart LR
    subgraph "TaskExecutor"
        PutTask[put_task] -->|envelope| Q[TaskInQueue]
        Q --> D[Dispatch]
        D --> W[worker]
        W -->|success| SP[process_task_success]
        SP --> Counter[success_counter]
        SP --> Downstream[(下流ノード)]
    end

    subgraph "TaskSplitter"
        Q2[TaskInQueue] --> DS[_split]
        DS --> PSR[process_task_success]
        PSR -->|list result| PSR_put[_put_split_result]
        PSR_put --> SC[split_counter]
        PSR_put --> Down2[(下流ノード per item)]
    end

    subgraph "TaskRouter"
        Q3[TaskInQueue] --> DR[_route]
        DR -->|target,task| PR[process_task_success]
        PR --> RC[route_counters target]
        PR --> Down3[(指定下流ノード)]
    end
```

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestTaskExecutor` | 17 | 3 つの実行モード、retry ヒット / 非ヒット、duplicate デフォルト値、sqlite リプレイ（error_type フィルタ含む）、永続化、コールバックシグネチャ検証 |
| `TestTaskSplitter` | 5 | デフォルトパラメータ、グラフ統合、空イテラブル、ジェネレータ、カスタム `split_item` |
| `TestTaskRouter` | 4 | デフォルトパラメータ、`_route` での未知 target 拒否、グラフ統合、安定ロック |
| **合計** | **26** | |

## 実行方法

```bash
# すべて実行
pytest tests/node/test_nodes.py -v

# TaskExecutor テストのみ
pytest tests/node/test_nodes.py -k "TaskExecutor" -v

# TaskSplitter テストのみ
pytest tests/node/test_nodes.py -k "TaskSplitter" -v

# TaskRouter テストのみ
pytest tests/node/test_nodes.py -k "TaskRouter" -v

# 重複チェック関連ケースのみ
pytest tests/node/test_nodes.py -k "duplicate" -v

# sqlite リプレイケースのみ
pytest tests/node/test_nodes.py -k "restore_db" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------|------|
| `TestTaskExecutor` | < 2.0s（sqlite 永続化とリプレイを含む） |
| `TestTaskSplitter` | < 1.0s |
| `TestTaskRouter` | < 1.0s |

## 注意事項

- `test_duplicate_check_disabled_by_default` は回帰テストで、`enable_duplicate_check` のデフォルトが `False` であることを保証し、ハッシュコストを削減して Web 側の再試行セマンティクスをサポートします。
- `test_restore_db*` ケースは `append_records` で sqlite に直接書き込み、`load_tasks_grouped_by_stage` のリプレイロジックを検証します。レコードの `stage` フィールドはノード名（`TaskGraph` の `set_nodes` と一致）です。
- `test_router_binding_counter_uses_stable_metrics_lock` は回帰テストで、過去の `route_counters` がモード切替で `TaskMetrics` が再構築されることでロック参照を失う問題をカバーします。現在のバージョンでは `metrics.lock` が一貫して使用されます。
- 非同期ケースには `pytest-asyncio` プラグインが必要です（プロジェクトで `pytest.mark.asyncio` を設定済み）。
- 永続化関連ケースはグローバルの `LifecycleSpout` / `LogSpout` に依存します。分離したい場合はカスタム fixture で明示的に `start()` / `stop()` してください。
- 関連実装は `src/celestialflow/node/core_nodes.py` にあります。
