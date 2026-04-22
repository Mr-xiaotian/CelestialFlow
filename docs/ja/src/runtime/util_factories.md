# RuntimeFactories

`runtime/util_factories.py` は、実行モードに基づいて対応するキュー、カウンターなどのオブジェクトを作成するためのランタイムオブジェクトのファクトリ関数を提供します。

## 設計目標

- serial/thread/process/async の基盤リソース作成ロジックを統一します
- モード間の実装の違いをカプセル化します
- 上位層コードの条件分岐を簡素化します

---

## 主要関数

### make_counter

実行モードに基づいて適切な実装を選択し、カウンターを作成します。

```python
def make_counter(
    mode: str, *, lock: LockType | None = None, init: int = 0
) -> ValueWrapper:
    """
    カウンターを返します。

    :param mode: 実行モード ('serial', 'thread', 'process', 'async')
    :param lock: オプションのロックオブジェクト（thread モードで使用）
    :param init: 初期値
    :return: ValueWrapper または MPValue
    """
```

戻り値の型:
- `process` モード: `MPValue("i", init)`
- `thread` モード: `ValueWrapper(init, lock=lock or Lock())`
- `serial`/`async` モード: `ValueWrapper(init)`

### make_queue_backend

単一チャネルキューを作成するためのキュークラス/コンストラクタを返します。

```python
def make_queue_backend(mode: str):
    """
    キュークラスを返します。

    :param mode: 実行モード
    :return: キュークラス
    """
```

戻り値の型:
- `async` モード: `AsyncQueue`
- `thread`/`serial`/`process` モード: `ThreadQueue`

> 注意: `process` モードも `ThreadQueue` を使用します。キューはノード内部で使用され、プロセス間をまたがないためです。

### make_task_in_queue

タスク入力キューのインスタンスを作成します。

```python
def make_task_in_queue(
    *,
    mode: str,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    TaskInQueue インスタンスを構築します。

    :param mode: 実行モード
    :param executor: タスクエグゼキューター
    :return: TaskInQueue インスタンス
    """
```

内部実装:
```python
Q = make_queue_backend(mode)
return TaskInQueue(
    queue=Q(),
    queue_tags=[],
    out_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

### make_task_out_queue

タスク出力キューのインスタンスを作成します。

```python
def make_task_out_queue(
    *,
    mode: str,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    TaskOutQueue インスタンスを構築します。

    :param mode: 実行モード
    :param executor: タスクエグゼキューター
    :return: TaskOutQueue インスタンス
    """
```

内部実装:
```python
Q = make_queue_backend(mode)
return TaskOutQueue(
    queue_list=[Q()],
    queue_tags=[None],
    in_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

---

## 使用例

### TaskExecutor での使用

```python
from celestialflow.runtime.util_factories import (
    make_counter,
    make_queue_backend,
    make_task_in_queue,
    make_task_out_queue,
)

# カウンターを作成
counter = make_counter("thread", init=0)

# キューバックエンドを作成
QueueClass = make_queue_backend("async")
queue = QueueClass()

# タスク入力キューを作成
in_queue = make_task_in_queue(mode="thread", executor=executor)

# タスク出力キューを作成
out_queue = make_task_out_queue(mode="thread", executor=executor)
```

### キューの直接作成

```python
# キュークラスを取得
ThreadQueue = make_queue_backend("thread")
AsyncQueue = make_queue_backend("async")

# インスタンスを作成
sync_queue = ThreadQueue()
async_queue = AsyncQueue()
```

---

## モード対照表

| モード | カウンター | キューバックエンド |
|--------|-----------|-------------------|
| `serial` | `ValueWrapper` | `ThreadQueue` |
| `thread` | `ValueWrapper` + Lock | `ThreadQueue` |
| `process` | `MPValue` | `ThreadQueue` |
| `async` | `ValueWrapper` | `AsyncQueue` |

---

## 注意事項

1. **プロセスモードのキュー**: 現在の実装では、`process` モードは `ThreadQueue` を使用しています。キューはノード内部で使用されるためです。プロセス間通信が必要な場合は、`MPQueue` に変更する必要があります。

2. **ロックの受け渡し**: `make_counter` の `lock` パラメータは、thread モードでロックオブジェクトを再利用するために使用されます。

3. **エグゼキューター依存**: `make_task_in_queue` と `make_task_out_queue` は、タグとロガーを取得するために `TaskExecutor` インスタンスが必要です。
