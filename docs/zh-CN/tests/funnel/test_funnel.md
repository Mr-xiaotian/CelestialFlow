# Funnel 核心测试 (test_funnel.py)

> 最后更新日期: 2026/05/23

## 作用
测试 `celestialflow.funnel` 模块的核心组件，包括 `BaseSpout` 和 `BaseInlet` 的交互逻辑。

## 核心测试对象
- `BaseSpout`: 抽象数据出口基类。
- `BaseInlet`: 数据入口基类。

## 关键测试流程
1. **生命周期管理**: 验证 `BaseSpout` 的 `start()` 和 `stop()` 流程，确保 `_before_start` 和 `_after_stop` 钩子被正确调用。
2. **异步通信**: 通过 `Queue` 验证 `Inlet` 发送的数据能被 `Spout` 正确接收并处理。
3. **终止信号处理**: 模拟发送 `TerminationSignal` 确保 `Spout` 线程能够优雅退出。

## 测试重点
- **线程安全性**: 验证 `Spout` 在独立线程中运行且能被外部 `stop()` 指令安全关闭。
- **错误捕获**: 确保直接实例化 `BaseSpout` 并调用未实现的 `_handle_record` 会抛出 `CelestialFlowError`。
- **断言意图**: 验证数据包在传递过程中的完整性，以及生命周期状态位的正确性。

## 重要细节
- 使用 `MockSpout` 和 `MockInlet` 子类化基类以测试具体行为。
- `test_spout_termination_signal` 中通过 `join(timeout=2)` 确保线程回收，避免测试挂起。

## 运行方式

```bash
# 全部执行
pytest tests/funnel/test_funnel.py -v

# 仅运行生命周期测试
pytest tests/funnel/test_funnel.py::TestFunnelCore::test_base_spout_lifecycle -v

# 仅运行终止信号测试
pytest tests/funnel/test_funnel.py -k "termination" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestFunnelCore` | ~1s（含线程同步等待） |

## 注意事项
- 测试涉及多线程同步，使用了 `time.sleep(0.1)` 等待异步处理完成。
- 若线程回收超时，`join(timeout=2)` 会强制退出，此时测试可能失败。
