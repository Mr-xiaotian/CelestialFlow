# 运行时类型测试 (test_types.py)

> 📅 最后更新日期: 2026/07/16

## 作用
验证 `celestialflow.runtime.util_types` 中的值对象、枚举和包装器，包括终止信号、无操作上下文、可选加锁值包装器、求和计数器以及任务事件常量。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestUtilTypes` | 28 | `TerminationSignal` 默认/自定义/部分参数构造；`TerminationIdPool` 非空/空/单元素构造；`NoOpContext` with 语句/异常透传/直接调用 enter/exit；`ValueWrapper` 基本读写/带锁读写/上下文管理器/`get_lock` 返回锁或 NoOpContext/负数值边界；`SumCounter` 累加/初始值/reset 清零/空计数器/多次 add；`StageStatus` 枚举值/IntEnum 行为/成员数量；`CTreeEvent` 任务常量/终止常量/前缀格式 |

## 覆盖点
- `TerminationSignal` / `TerminationIdPool` 的构造语义。
- `NoOpContext` 的上下文管理行为与异常透传。
- `ValueWrapper` 在带锁和不带锁两种模式下的读写语义。
- `SumCounter` 的累加、重置表现。
- `StageStatus`、`CTreeEvent` 的枚举值。

## 关键场景
- `ValueWrapper.get_lock()` 在不同构造方式下返回真实锁或 `NoOpContext`。
- `SumCounter.reset()` 会同时清零初始值和子计数器。

## 运行方式

```bash
pytest tests/runtime/test_types.py -v
pytest tests/runtime/test_types.py -k "value_wrapper or sum_counter" -v
pytest tests/runtime/test_types.py -k "termination" -v
```
