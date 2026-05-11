# bench_graph_mode.py 基准测试说明

> 📅 最后更新日期: 2026/05/11

## 目标

对比不同 `stage_mode`（`serial` / `thread`）和 `execution_mode`（`serial` / `thread` / `async`）组合下，复杂 DAG 的任务图执行性能。使用框架内置的 `benchmark_graph` 工具进行矩阵式对比。

## 测试内容

### `bench_graph_0`
- **结构**：4 节点 DAG（`stage1 → [stage2, stage3] → stage4`）
- **任务混合**：CPU 密集型（斐波那契）、I/O 密集型（sleep）、纯计算（除二、平方）
- **输入**：`range(25, 32) + [0, 27, None, 0, ""]`（含异常边界）
- **启用服务**：Reporter

### `bench_graph_1`
- **结构**：6 节点多层 DAG（A → [B, C] → [D, E] → F）
- **任务**：随机 0-2 秒睡眠（模拟不均匀负载）
- **输入**：`range(10)`
- **启用服务**：Reporter

## 关键配置

- `stage_modes = ["serial", "thread"]`
- `execution_sync_modes = ["serial", "thread"]`
- `execution_async_modes = ["async"]`
- 共 **6 种组合**，每种都会完整跑一遍图
- 需要分别提供 `sync_graph`（同步函数）和 `async_graph`（异步函数）

## 可能出现的问题

1. **环境变量依赖**：`REPORT_HOST` 等必须从 `.env` 加载，若未配置会导致 reporter 连接失败。
2. **总耗时长**：`benchmark_graph` 会运行 `len(stage_modes) × len(execution_modes)` 次完整图执行，含 I/O 延迟时总时间可达数分钟。

## 运行方式

```bash
python bench/bench_graph_mode.py
```

## 基准结果（实测）

> 环境：Windows，Python 3.10

### `bench_graph_0` — 4 节点 DAG，CPU+I/O 混合，11 个任务（含异常边界）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |

- `thread` 与 `serial` stage_mode 在 CPU 密集型（斐波那契）场景下差异不大（GIL 限制）
- `execution_mode=thread` 和 `async` 均有 2-3x 加速（斐波那契计算释放 GIL 的部分 + sleep 阶段的 I/O 并发）
- `async` 与 `thread` 性能接近，async 在 I/O 密集场景下略有优势

### `bench_graph_1` — 6 节点 DAG，I/O 密集（随机 sleep），10 个任务

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |

- 最优组合：`thread` + `async`（6.05s），比最差组合 `serial`+`serial`（54.25s）快 **9.0x**
- `async` 在 I/O 密集场景下优于 `thread`（协程切换开销小于线程切换）
- `thread`（线程布局）在 I/O 密集场景下显著优于 `serial`（单线程串行布局），各 stage 可并行启动

### 总结

- `stage_mode=thread` 在 I/O 密集场景下是最优选择
- `execution_mode=async` 在 I/O 密集场景下表现最佳，`thread` 次之，`serial` 最慢
- `async` 需要 stage 的函数为 async 函数，因此需要分别提供 sync_graph 和 async_graph
- 总耗时包含：线程启动 + 任务执行 + 队列传输 + 终止信号传播

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部服务：Reporter 服务（可选）
