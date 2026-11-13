# tests/conftest.py

> 📅 最后更新日期: 2026/11/13

## 作用

作为整个 `tests/` 目录的根级配置文件，负责加载环境变量并提供通用的测试辅助函数，统一测试中针对后台线程同步、运行节点指标观察者与生命周期数据库的访问方式。

## 核心功能

### 环境变量加载

- 自动调用 `dotenv.load_dotenv()`，确保项目根目录下的 `.env` 文件中的配置在测试启动时可用。

### 通用测试辅助函数

| 函数 | 用途 | 关键参数 / 行为 |
|------|------|----------------|
| `metrics_of(node)` | 取回节点 hub 上的 `MetricsObserver`，供断言读取指标 | 调用 `node.observers.find(MetricsObserver)`；未注册时抛 `AssertionError` |
| `lifecycle_db_of(target)` | 取回目标对象 hub 上的生命周期数据库路径 | 对任务图调用 `target.get_observers()`，对节点读取 `target.observers`，再 `find(LifecycleObserver)` 并返回其 `db_path`；未注册或未启动（`db_path is None`）时抛 `AssertionError` |
| `wait_until(condition, *, timeout, interval, message)` | 轮询等待条件成立，统一后台线程同步写法 | `timeout=5.0`、`interval=0.05`；超时后再检查一次，仍未成立则 `pytest.fail(message)` |
| `assert_stays_true(condition, *, duration, interval, message)` | 在一小段时间内持续验证条件保持为真 | `duration=0.3`、`interval=0.05`；任一采样点不成立即 `pytest.fail(message)` |

> **说明**：节点自身不再持有 `metrics` / `lifecycle` 字段，相关观察者由运行入口注册到 `node.observers`。`ObserverHub.find()` 会先查本层、再递归进入嵌套 hub，因此图运行时注入的图级观察者也能被 `metrics_of(graph)` / `lifecycle_db_of(graph)` 找到。

> `wait_until` 常用于等待 spout 后台线程消费完毕或 lifecycle / log 落盘；`assert_stays_true` 用于验证停止后的 spout 不再继续处理新记录。

## 注意事项

- 该文件会自动被 Pytest 识别为根级 `conftest.py`。
- 该文件不定义任何 `pytest.fixture`，仅提供 `metrics_of` / `lifecycle_db_of` / `wait_until` / `assert_stays_true` 四个测试辅助函数与 `.env` 加载逻辑。如需新增全局级别 Fixture，应在此文件中定义。
- `lifecycle_db_of` 要求 `LifecycleObserver` 已通过 `start()` 完成初始化，否则 `db_path` 为 `None` 会触发断言失败。
