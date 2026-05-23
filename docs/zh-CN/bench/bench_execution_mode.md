# bench_execution_mode.py 基准测试说明

> 📅 最后更新日期: 2026/05/24

## 目标

对比 `TaskExecutor` 在三种执行模式（`serial`、`thread`、`async`）下处理 CPU 密集型任务（斐波那契）和 I/O 密集型任务（sleep）的性能差异。使用框架内置的 `benchmark_executor` 工具统一输出对比报告。

> ⚠️ **重要说明**：同步版 `fibonacci` 与异步版 `fibonacci_async` 使用了**不同的算法**，详见下文分析。

## 测试内容

### `bench_executor_fibonacci`
- **任务**：计算斐波那契数列（`n=25..31`），含异常输入（`0, None, ""`）
- **配置**：`max_workers=6`，`max_retries=1`，重试 `ValueError`
- **对比模式**：`serial`、`thread`、`async`

#### 两种斐波那契实现的算法差异

| 版本 | 函数 | 算法 | 时间复杂度 |
|------|------|------|-----------|
| 同步（serial/thread 使用） | `fibonacci` | 递归双分支 | O(φⁿ) — 指数级 |
| 异步（async 使用） | `fibonacci_async` | 迭代累加 | O(n) — 线性 |

```python
# 同步版 — 递归，n=31 时递归调用约 200 万次
def fibonacci(n):
    if n <= 0:
        raise ValueError(...)
    elif n == 1:
        return 1
    elif n == 2:
        return 1
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

# 异步版 — 迭代，每 8 轮让出控制权
async def fibonacci_async(n):
    ...
    prev, curr = 1, 1
    for i in range(3, n + 1):
        prev, curr = curr, prev + curr
        if i % 8 == 0:
            await asyncio.sleep(0)  # 让出事件循环
    return curr
```

这意味着 async 模式的计算量本身就比 serial/thread 模式少几个数量级。**下方实测结果中的性能差异主要由算法不同主导，不能归因于执行模式本身的优劣。**

### `bench_executor_sleep`
- **任务**：纯睡眠 1 秒（模拟 I/O 等待），同步和异步版行为完全一致
- **配置**：`max_workers=12`，`max_retries=0`
- **对比模式**：`serial`、`thread`、`async`

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_workers` | 6 (CPU) / 12 (I/O) | 并发 worker 数 |
| `max_retries` | 1 (CPU) / 0 (I/O) | 重试次数 |

## 可能出现的问题

1. **斐波那契异步与同步算法不同**：如上所述，两者不可直接横向对比。该测试的设计意图是展示框架能否正确调度不同类型的任务函数，而非算法层面的公平对比。
2. **`asyncio` 事件循环冲突**：`main()` 使用 `asyncio.run()`，在 Jupyter 或已有事件循环的环境中运行会报错。
3. **`benchmark_executor` 输出格式**：该工具会改变 `TaskExecutor` 的 `execution_mode` 多次并重复运行，总耗时 = 模式数 × 任务数 × 单任务耗时，完整跑完可能需要数分钟。
4. **递归深度限制**：同步版 `fibonacci(31)` 递归深度约 200 万层，Python 默认递归限制（`sys.getrecursionlimit()` 通常为 1000）可能导致 `RecursionError`——但 Python 函数调用栈在递归分解中会深度展开；实际执行中 n=31 时递归树节点数约 200 万，但调用栈深度仅约 31 层（线性递归深度），因此通常不会触发限制。

## 运行方式

```bash
python bench/bench_execution_mode.py
```

## 参数调整

### 单独运行某个测试场景

在 `bench/bench_execution_mode.py` 的 `main()` 中可选择性运行：

```python
async def main():
    # 仅运行斐波那契测试
    await bench_executor_fibonacci()
    # await bench_executor_sleep()  # 注释掉 sleep 测试
```

```bash
# 修改后运行
python bench/bench_execution_mode.py
```

### 调整并发 Worker 数

各场景的 `max_workers` 在 `main()` 中直接设置：

```python
# 增大斐波那契的 worker 数
await bench_executor_fibonacci(max_workers=12)

# 调整 sleep 场景的 worker 数
await bench_executor_sleep(max_workers=4)
```

### 修改重试次数

```python
# 关闭重试
await bench_executor_fibonacci(max_retries=0)

# 增加重试次数
await bench_executor_fibonacci(max_retries=3)
```

### 自定义输入范围

斐波那契测试的输入在函数内部定义，可修改 `numbers` 列表：

```python
# 仅测试小数值（快速验证）
numbers = [10, 15, 20]

# 扩大范围
numbers = list(range(20, 35))
```

## 基准结果（实测）

> 环境：Windows，Python 3.10

### 场景一：斐波那契（CPU 密集型）
输入 12 个任务（含 5 个异常边界），max_workers=6，max_retries=1

| 模式 | 耗时 | 算法 | 说明 |
|------|------|------|------|
| serial | 0.896s | 递归 O(φⁿ) | 单线程顺序执行 |
| thread | 0.862s | 递归 O(φⁿ) | 6 线程并发，受 GIL 限制提升有限 |
| async | 0.009s | 迭代 O(n) | **算法不同** — 迭代 O(n) vs 递归 O(φⁿ) |

> 🔴 **关键警告**：serial/thread（递归 O(φⁿ)）与 async（迭代 O(n)）**使用了完全不同的斐波那契算法**，计算量相差多个数量级。二者耗时差异（~100x）**几乎全部来自算法复杂度本身**，**不可直接比较执行模式的优劣**。如需公平对比，三种模式应运行完全相同的任务函数。

### 场景二：sleep_1（I/O 密集型）
输入 12 个任务，每个睡眠 1 秒，max_workers=12。同步和异步版 sleep 行为一致，对比结果可直接反映执行模式差异。

| 模式 | 耗时 | 说明 |
|------|------|------|
| serial | 12.131s | 顺序睡眠，总耗时 ≈ 12 × 1s |
| thread | 1.028s | 12 线程并行，总耗时 ≈ 1s + 调度开销 |
| async | 1.024s | 协程并行，与 thread 基本持平 |

**关键结论**：
- **I/O 密集型任务**：thread 和 async 均能实现近乎理论最优的并行度（~12x 加速），两者差距可忽略
- **CPU 密集型任务**：应使用相同算法的函数进行公平对比；本例中 serial 与 thread 均为递归版斐波那契，thread 仅微弱优势（GIL 限制），async 使用了不同算法所以无法直接比较
- 如需公平对比执行模式，应让三种模式运行**相同的任务函数**，且该函数应包含 `await` 点（对 async）或 `time.sleep`（对 thread）以体现并发优势

## 依赖

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
