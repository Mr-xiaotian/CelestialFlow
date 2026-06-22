# 运行时类型测试 (test_types.py)

> 📅 最后更新日期: 2026/06/22

## 作用
验证 `celestialflow.runtime.util_types` 中的值对象、枚举和包装器，包括终止信号、无操作上下文、可选加锁值包装器、求和计数器以及任务事件常量。

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
