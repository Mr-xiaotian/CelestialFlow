# RuntimeFactories

> 📅 最終更新日: 2026/05/15

`runtime/util_factories.py` はランタイムオブジェクトのファクトリ関数を提供し、対応するキューオブジェクトを作成するために使用されます。

## 設計目標

- キュー作成ロジックをカプセル化
- 上位層コードの条件判断を簡素化

---

## 主要関数

### make_task_in_queue

タスク入力キューインスタンスを作成します。

```python
def make_task_in_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskInQueue:
    """
    TaskInQueue インスタンスを構築します。

    :param queue: キューインスタンス
    :param executor: タスクエグゼキューター
    :return: TaskInQueue インスタンス
    """
```

内部実装：
```python
return TaskInQueue(
    queue=queue,
    queue_tags=[],
    out_tag=executor.get_tag(),
    log_inlet=executor.log_inlet,
)
```

### make_task_out_queue

タスク出力キューインスタンスを作成します。

```python
def make_task_out_queue(
    *,
    queue: Any,
    executor: "TaskExecutor",
) -> TaskOutQueue:
    """
    TaskOutQueue インスタンスを構築します。

    :param queue: キューインスタンス
    :param executor: タスクエグゼキューター
    :return: TaskOutQueue インスタンス
    """
```

内部実装：
```python
return TaskOutQueue(
    queue_list=[queue],
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
    make_task_in_queue,
    make_task_out_queue,
)

# タスク入力キューを作成
in_queue = make_task_in_queue(queue=queue, executor=executor)

# タスク出力キューを作成
out_queue = make_task_out_queue(queue=queue, executor=executor)
```

---

## 注意事項

1. **エグゼキューター依存**: `make_task_in_queue` と `make_task_out_queue` はタグとロガーを取得するために `TaskExecutor` インスタンスが必要です。
