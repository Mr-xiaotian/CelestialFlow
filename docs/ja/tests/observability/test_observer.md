# tests/observer/test_observer.py

> 📅 最終更新日: 2026/10/09

## 役割

`celestialflow.observer` の `Observer`（オブザーバー基底クラス）、`ObserverHub`（オブザーバー集約 hub）、組み込みの `PrintObserver` と実行ノード / タスクグラフ（`TaskExecutor` / `TaskGraph` / `TaskChain`）の間のコールバック契約を検証します。タスク実行ライフサイクルにおけるキーノードでオブザーバーの `on_task_*` イベントが正しくトリガーされること、`ObserverHub` が集約して配信し単一オブザーバーの例外を隔離できること、グラフレベルのオブザーバーが全ノードのライフサイクルイベントとグラフ開始 / 終了イベントを受信できることを確認します。

## コアテスト対象

| クラス / オブジェクト | ソース | 説明 |
|-----------|------|------|
| `Observer` | `celestialflow.observer` | オブザーバー基底クラス。`on_node_start` / `on_node_end` / `on_task_input` / `on_task_success` / `on_task_fail` / `on_task_skip` / `on_task_retry` / `on_termination_input` / `on_termination_merge` / `on_worker_crash` / `on_graph_start` / `on_graph_end` などのイベントコールバックを提供 |
| `ObserverHub` | `celestialflow.observer` | オブザーバー集約器。各 `on_*` メソッドを明示的に実装し登録済みオブザーバーへブロードキャスト。循環登録を拒否 |
| `PrintObserver` | `celestialflow` | 組み込みオブザーバー。構築引数は `name` で、`[<name>] start` / `[<name>] finish` のログを出力し、`total` / `succeeded` / `failed` カウントを保持 |
| `MetricsObserver` | `celestialflow.observer` | 指標オブザーバー。`metrics_of(executor)` 経由でノード指標を読み取るテスト |
| `TaskExecutor` / `TaskGraph` / `TaskChain` | `celestialflow` | 実行ホスト。ライフサイクル中にオブザーバーへイベントをトリガー |
| イベント型 | `celestialflow.observer` | `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent` / `WorkerCrashEvent` / `GraphStartEvent` / `GraphEndEvent` |

## テストカバレッジマトリックス

| テストクラス | ケース | カバレッジ対象 |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_receives_full_lifecycle` | オブザーバーが完全なライフサイクルを受信：1 個の `NodeStartEvent`、3 個の `TaskInputEvent`、3 個の `TaskSuccessEvent`、最後の 1 個の `NodeEndEvent`；外部入力の `from_node is None` |
| `TestExecutorObserver` | `test_task_success_event_carries_payload_and_ids` | `TaskSuccessEvent` がタスク、結果、増分の `task_id` / `success_id` を保持 |
| `TestExecutorObserver` | `test_print_observer` | `PrintObserver("PrintObserverTest")` が `[PrintObserverTest] start` / `finish` を出力し、`total=3` / `succeeded=2` / `failed=1` |
| `TestExecutorObserver` | `test_observer_with_errors` | 3 タスク中 2 成功 1 失敗、成功/失敗カウントが正確 |
| `TestExecutorObserver` | `test_observer_receives_skip_callback` | `on_task_skip` がスキップイベント（1 個）を受信 |
| `TestExecutorObserver` | `test_no_observer_works` | オブザーバー未マウントでもエグゼキュータは正常動作、`metrics_of().succeeded == 3` |
| `TestExecutorObserver` | `test_multiple_observers` | 複数オブザーバーが同時に同一コールバックを受信 |
| `TestExecutorObserver` | `test_task_input_reports_upstream_source` | タスクグラフの上流が配信したタスクが `from_node == "up"` を保持する入力イベントをトリガー |
| `TestExtendedObserver` | `test_observer_receives_retry_and_termination_events` | リトライと終了に関するイベント（`TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent`）もオブザーバーへ配信される |
| `TestObserverHub` | `test_hub_explicitly_overrides_every_observer_method` | 転送ドリフト防止：hub が `Observer` プロトコルの各 `on_*` メソッドを明示的に実装する必要がある |
| `TestObserverHub` | `test_hub_isolates_observer_exception` | 単一オブザーバーが例外をスローしても他のオブザーバーへの配信は中断せず、エラーを stderr へ転送 |
| `TestObserverHub` | `test_hub_handle_exception_backstops_failing_observer_handler` | オブザーバーの `handle_exception` 自身が例外をスローする場合、hub がフォールバックし配信を中断しない |
| `TestObserverHub` | `test_hub_rejects_cyclic_registration` | hub が循環参照を形成する登録（自身 / 相互）を拒否し、`ConfigurationError` を送出 |
| `TestGraphObserver` | `test_graph_observer_receives_all_nodes` | グラフレベルオブザーバーが全ノードの `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` を受信 |
| `TestGraphObserver` | `test_node_local_observer_runs_before_graph_observer` | 同一ノード内で、ノードローカルのオブザーバーがグラフレベルのオブザーバーより先に呼び出される |
| `TestGraphObserver` | `test_graph_hub_is_injected_as_object` | 注入されるのは hub オブジェクト自体：run の後に登録したグラフレベルオブザーバーも有効 |
| `TestGraphObserver` | `test_run_async_injects_graph_observers` | `run_async` パスでもグラフレベルオブザーバー注入が実行される |
| `TestGraphObserver` | `test_graph_observer_receives_graph_events` | グラフレベルオブザーバーが `GraphStartEvent` / `GraphEndEvent` を受信し、開始イベントがグラフメタ情報（`nodes` / `edges` / `source_nodes` / `node_meta` / `class_name` / `is_dag`）を保持 |
| `TestGraphObserver` | `test_structure_supports_graph_observer` | 構造クラス（`TaskChain`）もグラフレベルオブザーバーをサポート |
| `TestGraphObserver` | `test_graph_rejects_cycle_between_graph_and_node_hub` | node hub を graph hub へ登録すると、注入時に循環参照のため `ConfigurationError` が送出される |

## テストの重点

- **イベント順序**：`NodeStartEvent` が最初、`NodeEndEvent` が最後にトリガーされることを確認。ノードローカルのオブザーバーはグラフレベルのオブザーバーより先に呼び出される。
- **ペイロードと ID**：成功イベントがタスク、結果、独立した `task_id` / `success_id`（増分）を保持。
- **原因追跡**：上流が配信したタスクは `from_node` フィールドでソースノードを識別。
- **hub の例外隔離**：単一オブザーバーが例外（`handle_exception` 自身の例外を含む）をスローしても他のオブザーバーには影響せず、配信は中断しない。
- **循環保護**：オブザーバー / hub が循環参照を形成する登録を拒否。

## 重要な詳細

- `RecordingObserver`（全 `on_*` メソッドをオーバーライドしてイベントを収集）、`CountObserver` / `Counter` などの Mock クラスを使用してイベント配信を検証。
- `test_print_observer` は `redirect_stdout(io.StringIO())` で標準出力をキャプチャし、`[PrintObserverTest] start` / `finish` が含まれることをアサートし、オブザーバーの `total` / `succeeded` / `failed` カウンタを読み取ります。
- `test_hub_isolates_observer_exception` と `test_hub_handle_exception_backstops_failing_observer_handler` は `redirect_stderr` で hub が転送したエラー情報をキャプチャします。
- ほとんどのケースは `execution_mode="serial"` を使用し、イベントを順序通りにアサートできます。

## 実行方法

```bash
# 全部実行
pytest tests/observer/test_observer.py -v

# エグゼキュータオブザーバーテストのみ実行
pytest tests/observer/test_observer.py -k "Executor" -v

# ObserverHub テストのみ実行
pytest tests/observer/test_observer.py -k "Hub" -v

# グラフオブザーバーテストのみ実行
pytest tests/observer/test_observer.py -k "Graph" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|------|------|
| `TestExecutorObserver` | < 1.0s |
| `TestExtendedObserver` | < 0.5s |
| `TestObserverHub` | < 0.5s |
| `TestGraphObserver` | < 1.0s（グラフ構築と実行を含む） |

## 注意事項

- リファクタリング後のフック / ライフサイクルはオブザーバーの `on_task_*` イベントに変更されました。`TaskExecutor` / `TaskGraph` / `TaskChain` はマウントされたオブザーバー（または hub）を通じて対応するライフサイクルノードでイベントをトリガーします。
- オブザーバーパターンはフレームワークの監視、ログ、プログレスバーの基盤です。
- `PrintObserver.__init__(name)` はノード名の指定を要求し、全出力に `[name]` プレフィックスを付けて複数ノードのログ混同を避けます。
- テストコードは `tests/observer/test_observer.py` にあります。