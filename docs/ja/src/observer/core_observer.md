# src/celestialflow/observer/core_observer.py

> 📅 最終更新日: 2026/10/09

`core_observer.py` は実行器ライフサイクル観測者の**基底クラス** `Observer` を定義します。これはタスク / ノード / タスクグラフの全ライフサイクルのイベントコールバックインターフェースを宣言し、すべてのコールバックにはデフォルトの空実装が用意されています。実装側はこの基底クラスを継承し、関心のあるメソッドだけをオーバーライドできます。

## Observer

```python
class Observer:
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
    def on_task_retry(self, event: TaskRetryEvent) -> None: ...
    def on_termination_input(self, event: TerminationInputEvent) -> None: ...
    def on_termination_merge(self, event: TerminationMergeEvent) -> None: ...
    def on_worker_crash(self, event: WorkerCrashEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

すべてのイベントコールバックはデフォルトで空実装（ABC ではない）。サブクラスが必要に応じてオーバーライドします。コールバックの引数はすべて `core_event.py` で定義されたイベント `dataclass` です。

### イベントの説明

| コールバック | イベント | トリガー時期 |
|------|------|----------|
| `on_node_start` | `NodeStartEvent` | ノード起動（`BaseTaskNode._prepare_start`） |
| `on_node_end` | `NodeEndEvent` | ノード終了（`BaseTaskNode._finish_start`） |
| `on_task_input` | `TaskInputEvent` | タスクがノードの入力キューに入る |
| `on_task_success` | `TaskSuccessEvent` | タスクの成功処理 |
| `on_task_fail` | `TaskFailEvent` | タスクの最終失敗 |
| `on_task_skip` | `TaskSkipEvent` | タスクのスキップ |
| `on_task_retry` | `TaskRetryEvent` | タスク失敗だがリトライをトリガー |
| `on_termination_input` | `TerminationInputEvent` | 終了シグナルが入力キューに入る |
| `on_termination_merge` | `TerminationMergeEvent` | 複数ソースの終了シグナルがマージされる |
| `on_worker_crash` | `WorkerCrashEvent` | ワーカースレッド / コルーチンがフォールバック層で未処理例外を捕捉 |
| `on_graph_start` | `GraphStartEvent` | タスクグラフ起動 |
| `on_graph_end` | `GraphEndEvent` | タスクグラフ終了 |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

観測者のコールバック自身が例外を送出した場合、`ObserverHub` がその例外を捕捉し、**その観測者自身の** `handle_exception` を呼び出して処理します。デフォルト実装は例外トレースバックを標準エラーへ出力します。サブクラスはオーバーライドしてカスタム戦略（収集、報告、無視）を実装できます。`handle_exception` 自身がさらに例外を送出した場合、hub の `handle_exception` が最終フォールバックとして処理します。

## イベント配信メカニズム

`Observer` のイベントは**ノードが各観測者を直接呼び出すのではなく**、`ObserverHub` を介してブロードキャストされます：

- ノードは `ObserverHub`（`BaseTaskNode.observers`）を保持し、`add_observer()` で観測者を登録します；
- ノードはイベント発生時に `hub.on_*()` を呼び出し、hub は登録順に各観測者へ転送します；
- 単一の観測者コールバックが送出した例外は hub が捕捉し、その観測者の `handle_exception` に渡します。**他の観測者への配信を中断せず、フレームワーク経路へも逃げません**。

内蔵観測者（こちらも `Observer` のサブクラス）：

| クラス | 所在ファイル | 説明 |
|---|---------|------|
| `PrintObserver` | `core_observer_print.py` | `print` ベースのコンソール観測者 |
| `MetricsObserver` | `core_metrics.py` | イベントに基づいてノードのカウントと状態を維持する指標観測者 |
| `ObserverHub` | `core_hub.py` | 観測者の配信センター。自体も `Observer` |
| `LifecycleInlet` / `LogInlet` | `persist` | `run_node_resources` / `run_graph_resources` が組み立て、イベントを消費してディスクへ書き込み |

## 使用例

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} 失敗: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## 注意事項

1. **コールバック引数はイベントオブジェクト**：旧版 `BaseObserver`（コールバックが `count` などの基本パラメータを受ける）とは異なり、すべてのコールバックは対応するイベント `dataclass` を受け取り、利用できるフィールドがより豊富です。
2. **`handle_exception` は自動ラップされない**：コールバック自身が例外を送出しないことを保証できません——例外は hub に捕捉された後、この観測者の `handle_exception` に転送されます。hub が `handle_exception` 自体を再ラップすることはありませんが、hub の `handle_exception` がフォールバックします。
3. **継承であってインスタンス化ではない**：`Observer` 基底クラスはすべてのコールバックを開放します。実際の利用では通常それを継承し、必要なメソッドだけをオーバーライドします。