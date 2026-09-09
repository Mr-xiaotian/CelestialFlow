# tests/observability/test_observer.py

> 📅 最后更新日期: 2026/09/09

## 作用
验证 `celestialflow` 包导出的 `BaseObserver` 与 `TaskExecutor` 之间的回调契约，确保任务执行生命周期中的关键节点能正确触发 `BaseObserver` 的覆写方法。

## 核心测试对象
- `BaseObserver`: 来自 `celestialflow.observability`，观测器基类，提供 `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish` 等回调钩子。
- `TaskExecutor`: 来自 `celestialflow.node`，被观测的任务执行器（测试中通过顶层 `celestialflow` 包导入）。

## 测试覆盖矩阵

| 测试类 | 用例 | 覆盖目标 |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_lifecycle` | 完整生命周期回调：`on_start` 出现、`on_task_success` 回调次数等于任务数（3 次）、`on_finish` 最后触发 |
| `TestExecutorObserver` | `test_observer_with_errors` | 失败回调：3 个任务中 2 成功 1 失败，成功/失败计数准确 |
| `TestExecutorObserver` | `test_no_observer_works` | 未挂载 observer 时执行器正常运行，计数不受影响 |
| `TestExecutorObserver` | `test_multiple_observers` | 多个 observer 同时挂载，各自独立收到相同回调 |
| `TestExecutorObserver` | `test_remove_observer` | `remove_observer()` 解绑后不再收到任何回调 |

## 测试重点
- **事件顺序**: 确保 `on_start` 在前、`on_finish` 最后触发。
- **失败捕获**: 验证当任务抛出异常时，`on_task_fail` 被正确调用且计数准确。
- **观察器组合**: 验证多 observer 挂载与解绑（移除后无副作用）。

## 重要细节
- 使用 `RecordingObserver`、`CountObserver`、`Counter` 等 Mock 类来收集和验证事件。
- `RecordingObserver` 覆写 `on_start` / `on_task_success` / `on_task_fail` / `on_task_duplicate` / `on_tasks_added` / `on_finish`，其中 `on_task_success` 与 `on_task_fail` 显式声明 `count=1` 默认参数。
- `CountObserver` 仅覆写 `on_task_success` / `on_task_fail`，通过累加 `count` 字段实现聚合统计。
- `test_remove_observer` 通过 `executor.remove_observer(observer)` 解绑后再次 `run`，断言 `observer.count == 0`。
- 所有用例都使用 `execution_mode="serial"` 模式，便于按顺序断言事件。

## 运行方式

```bash
# 全部执行
pytest tests/observability/test_observer.py -v

# 仅运行生命周期回调测试
pytest tests/observability/test_observer.py -k "lifecycle" -v

# 仅运行动态管理测试（添加/移除观测器）
pytest tests/observability/test_observer.py -k "observer_remove" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestExecutorObserver` | ~2s（含任务执行） |

## 注意事项
- 观测器模式是框架实现监控、日志和进度条的基础。
- 测试代码位于 `tests/observability/test_observer.py`。
