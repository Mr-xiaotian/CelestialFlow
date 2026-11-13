# src/celestialflow/observer/core_print.py

> 📅 最終更新日: 2026/11/13

`core_print.py` はすぐに使えるコンソール観測者 `PrintObserver` を提供します。これは `Observer` を継承し、統一された `on_event` 内でイベント型ごとにカウントを更新し、タスク実行の進捗（起動、入力、成功、失敗、スキップ、終了）を `print` で標準出力に出力します。ローカルデバッグやサンプルデモに便利です。

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_event(self, event: Event) -> None: ...
```

### 構築パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `name` | `str` | **必須**。出力プレフィックスで、異なるノードの観測者を区別するために使用（`[name] ...` の形） |

コンストラクタ内部では 1 つの `Lock` を作成し、4 つのスレッドセーフな `ValueWrapper` カウンタにそれを共有させます：

| 属性 | 型 | 説明 |
|------|------|------|
| `total` | `ValueWrapper` | 現在のノードに入ったタスクの総数（外部注入 + 上流配信）。`TaskInputEvent` で累加 |
| `succeeded` | `ValueWrapper` | 成功タスク数。`TaskSuccessEvent` で累加 |
| `failed` | `ValueWrapper` | 失敗タスク数。`TaskFailEvent` で累加 |
| `skipped` | `ValueWrapper` | スキップタスク数。`TaskSkipEvent` で累加 |
| `name` | `str` | 保存された出力プレフィックス |

### イベント処理

`on_event` は `match` でディスパッチします；`TaskRetryEvent`、終了シグナルイベント、グラフレベルイベントなどは `case _: pass` に落ち、カウントも出力も行いません。

| イベント | 動作 |
|------|------|
| `NodeStartEvent` | `[{name}] start total={total}` を出力 |
| `NodeEndEvent` | `[{name}] finish total=..., skipped=..., succeeded=..., failed=...` を出力（いずれのカウンタも変更しない） |
| `TaskInputEvent` | `total += 1`、`[{name}] total=...(+1)` を出力 |
| `TaskSuccessEvent` | `succeeded += 1`、`[{name}] succeeded=...(+1), total=...` を出力 |
| `TaskFailEvent` | `failed += 1`、`[{name}] failed=...(+1), total=...` を出力 |
| `TaskSkipEvent` | `skipped += 1`、`[{name}] skipped=...(+1), total=...` を出力 |

> すべてのカウントは同一のロックを共有する `ValueWrapper` を通じて読み書きされるため、`thread` / `async` 実行モードでも安全に呼び出せます。

## 使用例

### ノードの観測者 hub に直接登録

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def double(x: int) -> int:
    return x * 2


executor = TaskExecutor("Doubler", double, execution_mode="thread", max_workers=4)
executor.add_observer(PrintObserver("Doubler"))
executor.run([1, 2, 3])
# コンソール出力は次のような形です：
# [Doubler] total=1(+1)
# [Doubler] total=2(+1)
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

> ノードは `run()` 内で先に `put_task()` によりタスクを注入してから起動するため、`NodeStartEvent` が出力する `total` には起動前に注入されたタスク数がすでに含まれています；`put_signal()` が送出する終了シグナルは `TerminationInputEvent` であり、`total` には計上されません。

### 最終統計を読み取る

```python
from celestialflow.node import TaskExecutor
from celestialflow.observer import PrintObserver


def may_fail(x: int) -> int:
    if x % 2 == 0:
        raise ValueError(f"bad {x}")
    return x


executor = TaskExecutor("Odd", may_fail)
observer = PrintObserver("Odd")
executor.add_observer(observer)
executor.run([1, 2, 3, 4])

print(observer.succeeded.get(), observer.failed.get())
```

### 手動でイベントを送出

```python
from celestialflow.observer import PrintObserver, TaskInputEvent, TaskSuccessEvent

observer = PrintObserver("Manual")
observer.on_event(
    TaskInputEvent(node="Manual", task="x", task_repr="'x'", input_id=1)
)
observer.on_event(
    TaskSuccessEvent(
        node="Manual",
        task="x",
        task_repr="'x'",
        result="xx",
        result_repr="'xx'",
        elapsed=0.01,
        task_id=1,
        success_id=2,
    )
)
print(observer.total.get(), observer.succeeded.get())  # 1 1
```

## 注意事項

1. **`name` は必須パラメータ**：コンストラクタ署名は `__init__(self, name: str)` で、出力プレフィックスを必ず渡す必要があります。
2. **`total` の口径**：`total` は現在のノードに入ったすべてのタスクを集計し、**外部注入と上流配信のタスクを両方含みます**（`TaskInputEvent` で累加）。
3. **単一イベントエントリ**：`on_event` のみをオーバーライドし、`match` でディスパッチします；`on_node_start` / `on_task_success` などの個別コールバックは存在しません。
4. **例外隔離**：`on_event` 内の例外は `ObserverHub` が捕捉し、その観測者の `handle_exception` に渡されます。ノード実行を中断しません。
