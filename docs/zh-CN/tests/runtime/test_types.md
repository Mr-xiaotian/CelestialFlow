# tests/runtime/test_types.py

> 📅 最后更新日期: 2026/09/24

## 作用
验证 `celestialflow.runtime.util_types` 中的值对象、上下文管理器、可选加锁值包装器、生命周期状态枚举与事件常量，确保它们在运行时被各类节点/队列正确使用。

## 核心测试对象
- `TerminationSignal`: 终止哨兵，携带 `id` 与 `source`。
- `TerminationIdPool`: 终止信号 ID 池。
- `NoOpContext`: 空上下文管理器，可用于关闭加锁。
- `ValueWrapper`: 线程安全计数器包装，可自建锁、复用外部锁或传入 `NoOpContext` 关闭加锁。
- `StageStatus`: 生命周期状态 `IntEnum`。
- `CTreeEvent`: 事件名称常量集合。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestUtilTypes` | 23 | `TerminationSignal` 默认/自定义/部分参数；`TerminationIdPool` 非空/空/单元素；`NoOpContext` with 语句/异常透传/直接调用 enter、exit；`ValueWrapper` 读写/带锁/上下文管理器/`get_lock` 返回锁或 `NoOpContext`/锁独立/负数值；`StageStatus` 枚举值/IntEnum 行为/成员数量；`CTreeEvent` 任务常量/终止常量/前缀格式 |

## 覆盖点
- `TerminationSignal` / `TerminationIdPool` 的构造语义。
- `NoOpContext` 的上下文管理行为与异常透传。
- `ValueWrapper` 在带锁、复用锁与关闭加锁三种模式下的读写语义。
- `StageStatus`、`CTreeEvent` 的枚举值。

## 关键场景
- `TerminationSignal` 默认 `id == -1`、`source == "input"`；支持 `_id`/`source` 部分关键字构造。
- `ValueWrapper.get_lock()` 在传入 `Lock` 时返回该锁，不传时返回自建真实锁，显式传入 `NoOpContext` 时返回该实例（读写不加锁）。
- 每个 `ValueWrapper` 自建的锁互相独立，不跨实例共享。
- `StageStatus` 为 `IntEnum`，可与整数比较，成员数为 3。
- `CTreeEvent.TASK_RETRY_PREFIX` 以点结尾。

## 运行方式

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or noop" -v
pytest tests/runtime/test_types.py -k "termination" -v
```

## 注意事项
- 测试代码位于 `tests/runtime/test_types.py`，对应实现位于 `src/celestialflow/runtime/util_types.py`。
