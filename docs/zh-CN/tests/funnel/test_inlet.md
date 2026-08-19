# Inlet 基础测试 (test_inlet.py)

> 📅 最后更新日期: 2026/08/19

## 作用
验证 `celestialflow.funnel.core_inlet.BaseInlet` 的最小职责：把调用方传入的数据经由 `_funnel()` 放入目标队列，并被运行中的 `BaseSpout` 子类消费。

## 覆盖点
- `MockInlet.send()` 通过 `_funnel()` 转发记录。
- `MockSpout` 从队列消费字符串和字典两类消息。
- 未启动消费者时，记录仍应先进入队列，供后续读取。

## 测试覆盖矩阵

| 测试类 | 用例 | 覆盖目标 |
|--------|------|----------|
| `TestBaseInlet` | `test_inlet_to_spout_communication` | 启动 spout 后 inlet 注入的两条消息最终被按顺序消费 |
| `TestBaseInlet` | `test_funnel_puts_record_into_queue` | 未启动 spout 时 `_funnel()` 直接将原始记录放入目标队列 |
| `TestBaseInlet` | `test_bind_spout_creates_bound_inlet` | `bind_spout()` 返回与目标 spout 共享状态的 inlet |

## 运行方式

```bash
pytest tests/funnel/test_inlet.py -v
pytest tests/funnel/test_inlet.py -k "communication" -v
```
