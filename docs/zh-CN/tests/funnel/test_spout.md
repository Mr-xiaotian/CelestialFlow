# Spout 基础测试 (test_spout.py)

> 📅 最后更新日期: 2026/06/22

## 作用
验证 `celestialflow.funnel.core_spout.BaseSpout` 的生命周期钩子、终止信号处理和抽象方法约束，确保监听线程能够按预期启动、停止并消费停止前的记录。

## 覆盖点
- `start()` 会调用 `_before_start()`。
- `stop()` 会触发 `_after_stop()`，并在停止后不再继续消费新记录。
- 基类未实现 `_handle_record()` 时应抛出 `CelestialFlowError`。

## 关键场景
- `test_base_spout_lifecycle`: 验证启停钩子和“停止前数据仍会被消费”。
- `test_spout_termination_signal`: 验证重复 `stop()` 可安全调用，且终止后不会再处理后续入队数据。
- `test_spout_can_restart_after_stop`: 验证 `stop()` 后再次 `start()` 能重新创建后台线程并继续消费。
- `test_spout_not_implemented_error`: 验证抽象方法未覆写时的错误提示。

## 运行方式

```bash
pytest tests/funnel/test_spout.py -v
pytest tests/funnel/test_spout.py -k "lifecycle or termination" -v
```
