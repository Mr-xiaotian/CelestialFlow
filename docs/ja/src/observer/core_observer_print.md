# src/celestialflow/observer/core_observer_print.py

> 📅 最終更新日: 2026/10/09

`core_observer_print.py` はすぐに使えるコンソール観測者 `PrintObserver` を提供します。これは `Observer` を継承し、タスクの実行進捗（起動、入力、成功、失敗、スキップ、終了）を `print` で標準出力に出力します。ローカルデバッグやサンプルデモに便利です。

## PrintObserver

```python
class PrintObserver(Observer):
    def __init__(self, name: str) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...
```

### 構築パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `name` | `str` | **必須**。出力プレフィックスで、異なるノードの観測者を区別するために使用（`[name] ...` の形） |

コンストラクタ内部では 1 つの `Lock` を作成し、4 つのスレッドセーフな `ValueWrapper` カウンタを初期化します:

| 属性 | 型 | 説明 |
|------|------|------|
| `total` | `ValueWrapper` | 現在のノードに入ったタスクの総数（外部注入 + 上流配信）。`on_task_input` で累加 |
| `succeeded` | `ValueWrapper` | 成功タスク数。`on_task_success` で累加 |
| `failed` | `ValueWrapper` | 失敗タスク数。`on_task_fail` で累加 |
| `skipped` | `ValueWrapper` | スキップタスク数。`on_task_skip` で累加 |
| `name` | `str` | 保存された出力プレフィックス |

### コールバックの動作

| コールバック | 動作 |
|------|------|
| `on_node_start(event)` | `[{name}] start total={total}` を出力 |
| `on_node_end(event)` | `total += ...`、`[{name}] finish total=..., skipped=..., succeeded=..., failed=...` を出力 |
| `on_task_input(event)` | `total += 1`、`[{name}] total=...(+1)` を出力 |
| `on_task_success(event)` | `succeeded += 1`、`[{name}] succeeded=...(+1), total=...` を出力 |
| `on_task_fail(event)` | `failed += 1`、`[{name}] failed=...(+1), total=...` を出力 |
| `on_task_skip(event)` | `skipped += 1`、`[{name}] skipped=...(+1), total=...` を出力 |

> すべてのカウントは `ValueWrapper` を通じて共有ロックの保護下で読み書きされるため、`thread` / `async` 実行モードでも安全に呼び出せます。

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
# [Doubler] total=3(+1)
# [Doubler] start total=3
# [Doubler] succeeded=1(+1), total=3
# ...
# [Doubler] finish total=3, skipped=0, succeeded=3, failed=0
```

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

## 注意事項

1. **`name` は必須パラメータ**：コンストラクタ署名は `__init__(self, name: str)` で、出力プレフィックスを必ず渡す必要があります。
2. **`total` の口径**：`total` は現在のノードに入ったすべてのタスクを集計し、**外部注入と上流配信のタスクを両方含みます**（`on_task_input` で累加）。
3. **コールバック引数はイベントオブジェクト**：旧版の `count` 基本パラメータベースの観測者とは異なり、すべてのコールバックは `core_event.py` の対応する読み取り専用イベント `dataclass` を受け取ります。
4. **例外隔離**：コールバック内の例外は `ObserverHub` が捕捉し、その観測者の `handle_exception` に渡されます。ノード実行を中断しません。