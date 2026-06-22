# 观测器测试 (test_observer.py)

> 📅 最后更新日期: 2026/06/22

## 作用
验证 `celestialflow.observability` 模块中的观测器（Observer）机制，确保任务执行生命周期中的各个关键节点能正确触发回调。

## 核心测试对象
- `BaseObserver`: 观测器基类。
- `TaskExecutor`: 被观测的任务执行器。

## 关键测试流程
1. **生命周期回调**: 验证从 `on_start` 到 `on_finish` 的完整事件流，包括任务成功、失败和新增任务等事件。
2. **多观测器支持**: 验证多个观测器可以同时挂载到同一个执行器并独立接收事件。
3. **动态管理**: 验证观测器的动态添加与移除逻辑。

## 测试重点
- **事件顺序**: 确保 `on_start` 最先触发，`on_finish` 最后触发。
- **失败捕获**: 验证当任务抛出异常时，`on_task_fail` 被正确调用且计数准确。
- **默认行为**: 验证未覆写的方法走基类的空实现，不会引发异常。

## 重要细节
- 使用 `RecordingObserver` 和 `CountObserver` 等 Mock 类来收集和验证事件。
- `test_remove_observer` 确保解绑后的观测器不再产生副作用。

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
