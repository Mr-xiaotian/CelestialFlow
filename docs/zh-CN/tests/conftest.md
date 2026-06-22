# 全局测试配置 (conftest.py)

> 📅 最后更新日期: 2026/06/11

## 作用
作为整个 `tests/` 目录的根级配置文件，负责初始化测试环境、加载环境变量并提供通用测试辅助函数。

## 核心功能

### 环境变量加载
- 自动调用 `dotenv.load_dotenv()`，确保项目根目录下的 `.env` 文件中的配置在测试启动时可用。

### 通用测试辅助函数

| 函数 | 用途 | 关键参数 |
|------|------|----------|
| `wait_until(condition, *, timeout, interval, message)` | 轮询等待条件成立，统一后台线程同步写法 | `timeout=5.0`, `interval=0.05` |
| `assert_stays_true(condition, *, duration, interval, message)` | 在一小段时间内持续验证条件保持为真 | `duration=0.3`, `interval=0.05` |

> `wait_until` 常用于等待 spout 后台线程消费完毕；`assert_stays_true` 用于验证停止后的 spout 不再继续处理新记录。

## 注意事项
- 该文件会自动被 Pytest 识别。
- 如果需要添加全局级别的 Fixture，应在此文件中定义。
