# test_utils.py 测试工具说明

> 📅 最后更新日期: 2026/04/22

## 测试目标

`test_utils.py` 是测试套件的共享工具库，为单元测试和演示测试提供统一的测试函数、数据生成器和辅助类。所有测试任务函数均为**纯函数或受控副作用函数**，确保测试行为可预测、可重复。

## 测试范围

### 1. 通用计算函数
用于验证框架核心计算逻辑的数学函数：

| 函数 | 说明 | 特性 |
|------|------|------|
| `fibonacci(n)` | 递归斐波那契 | 输入 `n <= 0` 时抛出 `ValueError`，用于测试异常重试 |
| `fibonacci_async(n)` | 异步递归斐波那契 | 验证 `async` 执行模式 |
| `no_op(n)` | 恒等函数 | 无计算开销，用于基准测试对照 |
| `sum_int(*num)` | 整数求和 | 验证多参数解包 (`unpack_task_args=True`) |
| `add_one(num)` | 加一 | 最基础的线性变换 |
| `sqrt(num)` | 平方根 | 浮点运算验证 |
| `square(x)` | 平方 | 含 `sleep(1)` 延迟，模拟耗时任务 |

### 2. 带异常边界的运算函数

| 函数 | 触发条件 | 异常类型 |
|------|----------|----------|
| `add_offset(x, offset=10)` | `x > 30` | `ValueError` |
| `add_5` / `add_10` / `add_15` 等 | 同上（偏移量不同） | `ValueError` |

这些函数用于验证：
- 异常捕获与统计
- 重试机制（针对 `ValueError` 配置重试）
- 部分失败场景下的数据流连续性

### 3. Sleep 变体

| 函数 | 说明 |
|------|------|
| `sleep_1(n)` | 同步延迟 1 秒 |
| `sleep_1_async(n)` | 异步延迟 1 秒 |
| `add_one_sleep(n)` | 延迟 1 秒后加一，含多条件异常 |

### 4. URL 处理函数（demo_stages 专用）

模拟爬虫工作流的函数族：
- `generate_urls_sleep` / `log_urls_sleep` / `download_sleep` / `parse_sleep`
- 每个函数含 4-6 秒随机延迟，模拟 I/O 密集型任务
- `download_to_file` 使用 `requests` 进行真实 HTTP 请求

### 5. 特殊类

#### `RouterWrapper`
用于 `TaskRouter` 测试的路由包装器：
- 偶数路由到 `a_tag`
- 奇数路由到 `b_tag`
- 必须设置 `__name__` 属性以满足框架反射需求

## 可能的问题与注意事项

### 1. 含 `sleep` 的函数拖慢测试
`square`、`add_offset`、`sleep_1` 等函数包含硬编码的 `sleep(1)` 或随机 4-6 秒延迟。在单元测试中应避免直接使用这些函数，改用 `add_one`、`double` 等无延迟函数。

**解决方案**：
- 单元测试文件（如 `test_executor.py`）内部定义了独立的快速函数
- 演示测试（如 `demo_structure.py`）使用延迟函数以模拟真实负载

### 2. `fibonacci` 递归深度
`fibonacci(32)` 已有约 200 万次递归调用，可能导致：
- Python 递归深度限制（默认 1000）
- 测试执行时间过长

**建议**：单元测试中仅使用 `n <= 10` 的小数值。

### 3. `download_to_file` 的网络依赖
该函数发起真实 HTTP 请求，存在以下风险：
- 目标 URL 失效导致测试失败
- 网络波动导致超时
- 本地文件系统权限问题（`/tmp/` 路径在 Windows 上可能不存在）

**建议**：仅在演示环境中使用，单元测试中应使用 `responses` 或 `httpx.MockTransport` 进行模拟。

### 4. `random` 的非确定性
`generate_urls` 使用 `random.randint(1, 4)` 生成随机数量的 URL，导致：
- 每次运行的任务数不同
- 成功/失败计数难以精确断言

**建议**：如需精确断言，应在测试前设置随机种子 `random.seed(42)`。

## 运行方式

此文件本身不含测试用例，作为被导入的共享模块使用：
```python
from tests.test_utils import add_one, fibonacci
```

## 相关文件

- `tests/test_executor.py`：使用 `add_one`、`double` 等快速函数
- `tests/demo_executor.py`：使用 `fibonacci`、`sleep_1` 等演示函数
- `tests/demo_stages.py`：使用 URL 处理函数和 `RouterWrapper`
