# bench_executor.py 基准测试说明

## 目标

对比 `TaskExecutor` 在三种执行模式（`serial`、`thread`、`async`）下处理 CPU 密集型任务（斐波那契）和 I/O 密集型任务（sleep）的性能差异。使用框架内置的 `benchmark_executor` 工具统一输出对比报告。

## 测试内容

### `bench_executor_fibonacci`
- **任务**：递归计算斐波那契数列（`n=25..31`），含异常输入（`0, None, ""`）
- **配置**：`max_workers=6`，`max_retries=1`，重试 `ValueError`
- **对比模式**：`serial`、`thread`、`async`

### `bench_executor_sleep`
- **任务**：纯睡眠 1 秒（模拟 I/O 等待）
- **配置**：`max_workers=12`，`max_retries=0`
- **对比模式**：`serial`、`thread`、`async`

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `max_workers` | 6 (CPU) / 12 (I/O) | 并发 worker 数 |
| `max_retries` | 1 (CPU) / 0 (I/O) | 重试次数 |
| `show_progress` | `True` | 显示 tqdm 进度条 |

## 可能出现的问题

1. **递归深度限制**：`fibonacci` 使用递归实现，输入 `n=31` 时递归深度约 200 万，耗时数秒。若意外传入更大值可能导致 `RecursionError`。
2. **`asyncio` 事件循环冲突**：`main()` 使用 `asyncio.run()`，在 Jupyter 或已有事件循环的环境中运行会报错。
3. **`benchmark_executor` 输出格式**：该工具会改变 `TaskExecutor` 的 `execution_mode` 多次并重复运行，总耗时 = 模式数 × 任务数 × 单任务耗时，完整跑完可能需要数分钟。

## 运行方式

```bash
python bench/bench_executor.py
```

## 依赖

- `celestialflow`（`TaskExecutor`、`benchmark_executor`）
