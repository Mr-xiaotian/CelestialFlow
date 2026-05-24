# bench_execution_mode.py 基准测试说明

> 📅 最后更新日期: 2026/05/24

## 目标

对比 `TaskExecutor` 在三种执行模式（`serial`、`thread`、`async`）下处理 CPU 密集型任务（斐波那契）和 I/O 密集型任务（sleep）的性能差异。使用框架内置的 `benchmark_executor` 工具统一输出对比报告。

## 测试内容

### `bench_executor_fibonacci`
- **任务**：计算斐波那契数列（`n=25..31`），含异常输入（`0, None, ""`）
- **配置**：`max_workers=6`，`max_retries=1`，重试 `ValueError`
- **对比模式**：`serial`、`thread`、`async`

两种斐波那契实现**使用相同的迭代算法 O(n)**，确保公平对比：

```python
# 同步版 — 迭代，O(n)
def fibonacci(n):
    ...
    prev, curr = 1, 1
    for _ in range(3, n + 1):
        prev, curr = curr, prev + curr
    return curr

# 异步版 — 迭代 + 每 8 轮协程出让，O(n)
async def fibonacci_async(n):
    ...
    prev, curr = 1, 1
    for i in range(3, n + 1):
        prev, curr = curr, prev + curr
        if i % 8 == 0:
            await asyncio.sleep(0)  # 让出事件循环
    return curr
```

唯一差异是 `fibonacci_async` 每 8 次迭代有一处 `await` 出让点，这是 async 执行模式本身固有的协作式调度特性。

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

1. **CPU 密集任务受 GIL 限制**：Python 的 GIL 限制了同一时刻只有一个线程执行 Python 字节码。`thread` 模式下即便开了 6 个 worker，纯计算的大部分时间仍被 GIL 串行化。
2. **`asyncio` 事件循环冲突**：`main()` 使用 `asyncio.run()`，在 Jupyter 或已有事件循环的环境中运行会报错。
3. **`benchmark_executor` 输出格式**：该工具会改变 `TaskExecutor` 的 `execution_mode` 多次并重复运行，总耗时 = 模式数 × 任务数 × 单任务耗时。

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
输入 12 个任务（含 5 个异常边界），max_workers=6，max_retries=1。三种模式使用**相同的迭代 O(n) 算法**。

| 模式 | 耗时 | 说明 |
|------|------|------|
| serial | 0.0065s | 单线程顺序执行，纯计算无调度开销 |
| thread | 0.0048s | 6 线程并发，受 GIL 限制，提升有限 |
| async | 0.0062s | 协程并发，迭代中的 await 出让点允许并发，但仍受限于纯计算本质 |

> 🟢 三种模式耗时在同一量级（~5-6ms）。thread 略快是因为 GIL 在高频迭代的出让点之间仍有少量并发窗口；async 的 `await` 出让点带来了极微量的协程调度开销。整体差异在微秒级，对 CPU 密集任务三者均非明显加速。

### 场景二：sleep_1（I/O 密集型）
输入 12 个任务，每个睡眠 1 秒，max_workers=12。同步和异步版 sleep 行为一致，对比结果可直接反映执行模式差异。

| 模式 | 耗时 | 说明 |
|------|------|------|
| serial | 12.010s | 顺序睡眠，总耗时 ≈ 12 × 1s |
| thread | 1.006s | 12 线程并行，总耗时 ≈ 1s + 调度开销 |
| async | 1.009s | 协程并行，与 thread 基本持平 |

**关键结论**：
- **I/O 密集型任务**：thread 和 async 均能实现近乎理论最优的并行度（~12x 加速），两者差距可忽略
- **CPU 密集型任务**：三者耗时在同一量级。纯计算任务受 Python GIL 限制，thread 无显著优势；async 在协程出让点可并发但整体提升有限
- 选择执行模式的核心依据是**任务本质**：I/O 等待用 thread/async，纯计算考虑 GIL 影响（或考虑多进程）

## 依赖

- `celestialflow`（`TaskExecutor`、`TaskProgress`、`benchmark_executor`）
