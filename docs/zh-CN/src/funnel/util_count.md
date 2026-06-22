# PendingCounter

> 📅 最后更新日期: 2026/06/22

`funnel/util_count.py` 提供了一个线程安全的待处理计数器 `PendingCounter`，用于统计某个 `BaseSpout` 对应记录中尚未完成处理的数量。

## 核心对象

### PendingCounter

```python
class PendingCounter:
    def __init__(self) -> None: ...
    def increment(self) -> int: ...
    def decrement(self) -> int: ...
    def get_count(self) -> int: ...
```

`PendingCounter` 内部使用 `threading.Lock` 保护计数变量，因此可以在多线程环境下安全使用。

## 方法说明

| 方法 | 返回值 | 说明 |
|------|--------|------|
| `increment()` | `int` | 待处理数量加一，返回自增后的值 |
| `decrement()` | `int` | 待处理数量减一，返回自减后的值 |
| `get_count()` | `int` | 读取当前待处理数量 |

## 使用方式

`PendingCounter` 通常由 `BaseSpout` 在初始化时自动创建，用户一般不需要直接操作它。`BaseSpout.get_counter()` 和 `BaseSpout.get_pending_count()` 提供了外部访问入口：

```python
from celestialflow.funnel import BaseSpout

class PrintSpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

spout = PrintSpout()
spout.start()

spout.get_queue().put("task_1")
spout.get_queue().put("task_2")

print(f"待处理: {spout.get_pending_count()}")

spout.stop()
print(f"停止后待处理: {spout.get_pending_count()}")
```

## 注意事项

1. **统计口径**：`BaseSpout._spout()` 在记录出队后先调用 `_handle_record()`，处理完成（包括异常）后才调用 `decrement()`，因此 `get_pending_count()` 包含"已出队但仍在处理"的记录。
2. **回滚机制**：`BaseInlet._funnel()` 在入队前调用 `increment()`，若入队失败会立即调用 `decrement()` 回滚计数。
3. **线程安全**：所有操作均通过 `Lock` 保护，可在多生产者/单消费者场景下安全使用。
