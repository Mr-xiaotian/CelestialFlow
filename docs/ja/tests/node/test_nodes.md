# tests/node/test_nodes.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.node.core_nodes` 内の 3 つの具象ノードクラス `TaskExecutor` / `TaskSplitter` / `TaskRouter` の実行・分割・ルーティング挙動を検証します。直列 / スレッド / 非同期の 3 つの実行モード、sqlite からの永続化リプレイ、ノード初期化制約、ルーティングの未知 target エラー、紐付けが複数モードで安定することをカバーします。

## コアテスト対象

| クラス / 関数 | 役割 | 説明 |
|-----------|------|------|
| `TaskExecutor` | 被テスト対象 | 汎用エグゼキュータ。`serial` / `thread` / `async`、例外処理、retry、restore_db、結果永続化、扇出ペイロードの意味論を検証 |
| `TaskSplitter` | 被テスト対象 | 1→N スプリッタ。`downstream_counts`、空イテラブル、ジェネレータ、カスタム分割関数を検証 |
| `TaskRouter` | 被テスト対象 | ルータ。`func` は `dict[str, Y]` マッピングを返す；`downstream_counts`、未知 target 失敗のヒント、target 別配送、紐付けのモード横断的な安定を検証 |
| `append_records` | ユーティリティ | `celestialflow.persist.util_sqlite` から来て、failed / pending レコードを直接書き込み、リプレイテストに使用 |
| `load_task_error_records` / `load_task_result_records` | ユーティリティ | sqlite 内の task-error / task-result ペアを読み取り、ライフサイクル永続化の結果をアサートする |
| `build_result_dict` | ユーティリティ | `get_success_pairs` と `get_error_pairs` を集約して `{task: result_or_error_str}` を構築 |
| `_counts` | ユーティリティ | `metrics_of(node).get_node_metrics(name)` でノード指標スナップショットを取得し、旧フィールド名辞書にマッピングする |

## 主要テストシナリオ

### `TestTaskExecutor` — エグゼキュータ（15 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_serial_basic` | 直列実行 5 タスク、succeeded=5、failed=0、pending=0 |
| `test_serial_with_errors` | 直列実行 `[1,-1,2,-2,3]`、`PersistedError.error_type == "ValueError"`、succeeded=3 / failed=2 |
| `test_serial_retry` | `RuntimeError` をリトライ可能として登録；最初の 2 回失敗後、3 回目で `x+100` を返却、`call_count == 3` |
| `test_serial_no_retry_for_unmatched_exception` | 未登録のリトライ可能例外はリトライをトリガせず、直接 failed になる |
| `test_thread_basic` | スレッドモード（4 worker）で 5 タスクを正常処理 |
| `test_async_basic` | 非同期モードで 3 タスクを正常処理 |
| `test_async_double` | 非同期モードで 20 タスクを連続処理 |
| `test_restore_db` | デフォルトでは自ノード `node == self.get_name()` の failed / pending のみ読み取り、3 件の成功をリプレイ |
| `test_restore_db_filters_error_type_when_enabled` | `filter_by_error_type=True` + `set_retry_exceptions(RuntimeError)` 時、RuntimeError のみリプレイ |
| `test_restore_db_filter_keeps_pending_records` | フィルタ有効時でも `pending` レコードは常に保持される |
| `test_success_persist` | 成功結果が永続化された後、`get_success_pairs()` から読み戻せる |
| `test_rejects_zero_argument_func` | 0 引数関数は `ConfigurationError` を送出する |
| `test_rejects_multi_argument_func` | 多引数関数は `ConfigurationError` を送出する |
| `test_name_and_execution_mode` | `get_name()` と `execution_mode` が正しく公開される |
| `test_fanout_downstream_records_result_as_input` | 通常のエグゼキュータが扇出する際、下流は上流の入力ではなく上流の結果を記録する |

### `TestTaskSplitter` — スプリッタ（5 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_splitter_init` | デフォルト `execution_mode="serial"`、まだ下流に紐付けていない |
| `test_splitter_process_success` | `TaskGraph` 直列接続後の下流 `succeeded == 3`、`downstream_counts["A"] == 3` |
| `test_splitter_allows_empty_iterable` | 空イテラブルは例外を投げず、下流 succeeded=0、送信カウントなし |
| `test_splitter_supports_generator_input` | 一度きりジェネレータも完全に分割される（送信カウント=3） |
| `test_splitter_custom_func_transforms_items` | カスタム分割関数がサブタスクを変換してから分配し、下流の結果が `["a", "b", "c"]` になる |

### `TestTaskRouter` — ルータ（6 ケース）

| ケース | カバレッジ目標 |
|------|---------|
| `test_router_init` | デフォルト `serial`、まだ下流に紐付けていない |
| `test_router_func_returns_target_payload_map` | `func(task)` が `{target: payload}` マッピングを返す |
| `test_router_process_success` | `TaskGraph` 内の 2 つの下流 `target1` / `target2` がそれぞれ 1 件ずつ受信、`downstream_counts` もそれぞれ = 1 |
| `test_router_unknown_target_fails_with_hint` | 接続済み target へは正常に配送；未接続 target は失敗としてカウントされ、エラーメッセージに `Unknown target: ghost` と許可 target の一覧が含まれる |
| `test_router_dispatch_targets_receive_own_payload` | 1 回のルーティングで複数 target を返す場合、各下流はルータの入力ではなく自身のペイロードを受け取る |
| `test_router_binding_survives_mode_switch` | `connect_to` が確立した紐付けが `execution_mode` を切り替えても安定する |

## 主要データフロー

```mermaid
flowchart LR
    subgraph "TaskExecutor"
        PutTask[put_task] -->|envelope| Q[task_queue]
        Q --> D[Dispatch]
        D --> W[worker]
        W -->|success| SP[process_task_success]
        SP --> Counter[(metrics 計数)]
        SP --> Downstream[(下流ノード yield_queue)]
    end

    subgraph "TaskSplitter"
        Q2[task_queue] --> DS[分割関数]
        DS --> PSR[process_task_success]
        PSR -->|各サブタスク| PSR_put[yield_queue.put_target]
        PSR_put --> SC[(downstream_counts)]
        PSR_put --> Down2[(下流ノード per item)]
    end

    subgraph "TaskRouter"
        Q3[task_queue] --> DR[ルーティング関数]
        DR -->|dict target:payload| PR[process_task_success]
        PR --> RC[(downstream_counts)]
        PR --> Down3[(指定下流ノード)]
    end
```

> 指標カウントは `metrics_of(graph).get_node_metrics(name).downstream_counts` から読み取ります。`downstream_counts` はノード間の実際の送信回数のマッピングです（送信されていない辺は現れません）。

## テストカバレッジマトリクス

| テストクラス | ケース数 | カバレッジ目標 |
|--------|--------|---------|
| `TestTaskExecutor` | 15 | 3 つの実行モード、retry ヒット / 非ヒット、sqlite リプレイ（error_type フィルタ含む）、永続化、コールバックシグネチャ検証、扇出ペイロードの意味論 |
| `TestTaskSplitter` | 5 | デフォルトパラメータ、グラフ統合、空イテラブル、ジェネレータ、カスタム分割関数 |
| `TestTaskRouter` | 6 | デフォルトパラメータ、`func` の返すマッピング、グラフ統合、未知 target エラー、ペイロード別配送、紐付けのモード横断的な安定 |
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

- `test_restore_db*` ケースは `append_records` で sqlite に直接書き込み（レコードの `node` フィールドはノード名）、回復リプレイのロジックを検証します。
- `test_router_unknown_target_fails_with_hint` は `load_task_error_records` と `get_node_metrics(...).failed / processed` で未知 target の失敗をアサートします。エラー message に `Unknown target: <name>` と許可 target の一覧が含まれ、router 層で例外を送出しません。
- `test_router_binding_survives_mode_switch` と `test_connect_to_binding_survives_execution_mode_switch`（test_node.md 参照）はどちらも回帰テストで、紐付けが複数モードで安定する意味論をカバーします。
- 非同期ケースには `pytest-asyncio` プラグインが必要です（プロジェクトで `pytest.mark.asyncio` を設定済み）。
- 関連実装は `src/celestialflow/node/core_nodes.py` と `src/celestialflow/persist/util_sqlite.py` にあります。