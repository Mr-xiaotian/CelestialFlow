# tests/conftest.py

> 📅 最后更新日期: 2026/10/09

## 作用
作为整个 `tests/` 目录的根级配置文件，负责加载环境变量并提供通用的测试辅助函数，统一测试中针对后台线程同步与运行节点指标观察者的访问方式。

## 核心功能

### 环境变量加载
- 自动调用 `dotenv.load_dotenv()`，确保项目根目录下的 `.env` 文件中的配置在测试启动时可用。

### 通用测试辅助函数

| 函数 | 用途 | 关键参数 |
|------|------|----------|
| `metrics_of(node)` | 从运行节点的 `observers` hub 快照中取回 `MetricsObserver` 指标观察者，供断言读取节点指标 | 遍历 `node.observers._snapshot()`，找不到时抛 `AssertionError` |
| `wait_until(condition, *, timeout, interval, message)` | 轮询等待条件成立，统一后台线程同步写法 | `timeout=5.0`, `interval=0.05` |
| `assert_stays_true(condition, *, duration, interval, message)` | 在一小段时间内持续验证条件保持为真 | `duration=0.3`, `interval=0.05` |

> **说明**：节点自身不再持有 `metrics` 字段。重构后，指标观察者由运行入口注册到 `node.observers`，`metrics_of()` 从 hub 快照中取回该观察者，供测试断言读取（如 `metrics_of(executor).get_node_metrics(executor.get_name()).succeeded`）。

> `wait_until` 常用于等待 spout 后台线程消费完毕；`assert_stays_true` 用于验证停止后的 spout 不再继续处理新记录。

## 注意事项
- 该文件会自动被 Pytest 识别。
- 该文件不定义任何 `pytest.fixture`，仅提供 `metrics_of` / `wait_until` / `assert_stays_true` 三个测试辅助函数与 `.env` 加载逻辑。如需新增全局级别 Fixture，应在此文件中定义。
