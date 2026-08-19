# Spout 基础测试 (test_spout.py)

> 📅 最后更新日期: 2026/08/19

## 作用
验证 `celestialflow.funnel.core_spout.BaseSpout` 的生命周期钩子、终止信号处理和抽象方法约束，确保监听线程能够按预期启动、停止并消费停止前的记录。

## 覆盖点
- `start()` 会调用 `_before_start()`。
- `stop()` 会触发 `_after_stop()`，并在停止后不再继续消费新记录。
- 基类未实现 `_handle_record()` 时应抛出 `CelestialFlowError`。

## 测试覆盖矩阵

| 测试类 | 用例 | 覆盖目标 |
|--------|------|----------|
| `TestBaseSpout` | `test_base_spout_lifecycle` | 启停钩子正确触发，停止前的数据仍会被消费 |
| `TestBaseSpout` | `test_spout_termination_signal` | 重复 `stop()` 安全，终止后不再处理后续入队数据 |
| `TestBaseSpout` | `test_spout_can_restart_after_stop` | `stop()` 后再次 `start()` 重新创建后台线程并继续消费 |
| `TestBaseSpout` | `test_spout_not_implemented_error` | 抽象方法 `_handle_record` 未覆写时抛出 `CelestialFlowError` |

## 运行方式

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
