# Inlet 基础测试 (test_inlet.py)

> 最后更新日期: 2026/06/05

## 作用
验证 `celestialflow.funnel.core_inlet.BaseInlet` 的最小职责：把调用方传入的数据经由 `_funnel()` 放入目标队列，并被运行中的 `BaseSpout` 子类消费。

## 覆盖点
- `MockInlet.send()` 通过 `_funnel()` 转发记录。
- `MockSpout` 从队列消费字符串和字典两类消息。
- 未启动消费者时，记录仍应先进入队列，供后续读取。

## 关键场景
- `test_inlet_to_spout_communication`: 启动 `MockSpout` 后发送两条消息，验证消费者最终按顺序收到。
- `test_funnel_puts_record_into_queue`: 不启动 spout，直接断言队列里拿到原始记录，确认 `_funnel()` 不会改写数据。

## 运行方式

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
