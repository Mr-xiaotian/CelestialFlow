# src/celestialflow/observer/core_observer.py

> 📅 最終更新日: 2026/11/13

`core_observer.py` は実行器ライフサイクル観測者の**基底クラス** `Observer` を定義します。旧版の「イベントごとに 1 つのコールバック」とは異なり、現在はすべてのイベントが単一の `on_event` を通じて入ります。実装側はこの基底クラスを継承した後、このメソッドのみをオーバーライドし、`match` で具体イベント型ごとにディスパッチすれば、関心のないイベント型は自然に無視されます。

## Observer

```python
class Observer:
    def on_event(self, event: Event) -> None: ...

    def handle_exception(self, exception: Exception) -> None: ...
```

- `on_event`：**唯一**のイベントエントリ。デフォルト実装はすべてのイベントを無視します（メソッド本体は `...`）。
- `handle_exception`：観測者コールバック自身が例外を送出した際の処理コールバック。デフォルトではトレースバックを標準エラーへ出力します。

`Observer` は `ABC` ではなく、サブクラスが必要に応じてオーバーライドするだけです。イベントオブジェクトは `core_event.py` で定義され、すべて基底クラス `Event` を継承します。

### イベントのディスパッチ

サブクラスは通常、`on_event` 内で構造化パターンマッチを使って型ごとにディスパッチします：

```python
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} 失敗: {event.exception}")
            case _:
                pass
```

| イベント | トリガー時期 |
|------|----------|
| `NodeStartEvent` | ノード起動（`BaseTaskNode._prepare_start`） |
| `NodeEndEvent` | ノード終了（`BaseTaskNode._finish_start`） |
| `TaskInputEvent` | タスクがノードの入力キューに入る |
| `TaskSuccessEvent` | タスクの成功処理 |
| `TaskFailEvent` | タスクの最終失敗 |
| `TaskSkipEvent` | タスクのスキップ |
| `TaskRetryEvent` | タスク失敗だがリトライをトリガー |
| `TerminationInputEvent` | 終了シグナルが入力キューに入る |
| `TerminationMergeEvent` | 複数ソースの終了シグナルがマージされる |
| `GraphStartEvent` | タスクグラフ起動 |
| `GraphEndEvent` | タスクグラフ終了 |

### handle_exception

```python
def handle_exception(self, exception: Exception) -> None:
    traceback.print_exception(exception)
```

観測者の `on_event` 自身が例外を送出した場合、`ObserverHub` がその例外を捕捉し、**その観測者自身の** `handle_exception` を呼び出して処理します。デフォルト実装は例外トレースバックを標準エラーへ出力します。サブクラスはオーバーライドしてカスタム戦略（収集、報告、無視）を実装できます。`handle_exception` 自身がさらに例外を送出した場合、hub の `handle_exception` が最終フォールバックとして処理します。

## イベント配信メカニズム

`Observer` のイベントは**ノードが各観測者を個別に直接呼び出すのではなく**、`ObserverHub` を介してブロードキャストされます：

- ノードは `ObserverHub`（`BaseTaskNode.observers`）を保持し、`add_observer()` で観測者を登録します；
- ノードはイベント発生時に対応するイベントを構築して `hub.on_event(event)` を呼び出し、hub が登録順に各観測者へ転送します；
- 単一の観測者コールバックが送出した例外は hub が捕捉し、その観測者の `handle_exception` に渡します。**他の観測者への配信を中断せず、フレームワーク経路へも逃げません**。

内蔵観測者（こちらも `Observer` のサブクラス）：

| クラス | 所在ファイル | 説明 |
|---|---------|------|
| `PrintObserver` | `core_print.py` | `print` ベースのコンソール観測者 |
| `MetricsObserver` | `core_metrics.py` | イベントに基づいてノードのカウントと状態を維持する指標観測者 |
| `ObserverHub` | `core_hub.py` | 観測者の配信センター。自体も `Observer` |
| `LifecycleObserver` / `LogObserver` | `persist` | ライフサイクルとログの観測者。`run_node_resources` / `run_graph_resources` が組み立て |

## 使用例

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import Event, Observer, TaskFailEvent, TaskSuccessEvent


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case TaskFailEvent():
                print(f"{event.node} 失敗: {event.exception}")


executor = TaskExecutor("Test", lambda x: x * 2)
executor.add_observer(MyObserver())
executor.run([1, 2, 3])
```

## 注意事項

1. **単一コールバック**：すべてのイベントは `on_event` から入ります；旧版の `on_node_start` / `on_task_success` などの個別コールバックはすべて削除されました。
2. **`handle_exception` は自動ラップされない**：コールバック自身が例外を送出しないことを保証できません——例外は hub に捕捉された後、この観測者の `handle_exception` に転送されます。それ自体が hub に再ラップされることはありませんが、hub の `handle_exception` がフォールバックします。
3. **継承であってインスタンス化ではない**：`Observer` 基底クラスは `on_event` を開放します。実際の利用では通常それを継承し、必要な分岐だけをオーバーライドします。
