# bench_graph_mode.py 基准测试说明

> 📅 最后更新日期: 2026/07/16

## 目标

对比不同 `stage_mode`（`serial` / `thread`）和 `execution_mode`（`serial` / `thread` / `async`）组合下，复杂 DAG 的任务图执行性能。使用框架内置的 `benchmark_graph` 工具进行矩阵式对比。

## 测试内容

### `bench_graph_0`
- **结构**：4 节点 DAG，`stage1 → stage2 → stage4`，`stage1 → stage3`（stage3 为不汇入 stage4 的独立分支）
- **任务混合**：CPU 密集型（斐波那契）、I/O 密集型（sleep）、纯计算（除二、平方）
- **输入**：`range(25, 32) + [0, 27, None, 0, ""]`（含异常边界）
- **重试设置**：`stage1`、`stage2` 对 `ValueError` 启用 `max_retries=1`
- **启用服务**：Reporter

### `bench_graph_1`
- **结构**：6 节点多层 DAG（A → [B, C]；B → [D, E]；C → E；D → F）
- **任务**：随机 0-2 秒睡眠（模拟不均匀负载）
- **输入**：`range(10)`
- **启用服务**：Reporter

### `bench_graph_2`
- **结构**：4 节点 DAG（Splitter → A → [B, C]），使用 `TaskSplitter` 展开输入
- **任务**：纯计算（加一、乘二），测试框架调度吞吐上限
- **输入**：`range(10_000)`（经 Splitter 展开为 10,000 个独立任务）

## 关键配置

- `benchmark_graph` 内部会遍历 `stage_mode`（`serial` / `thread`）和 `execution_mode`（`serial` / `thread` / `async`）的组合，共 **6 种组合**，每种都会完整跑一遍图
- 本文件不直接配置这些模式，仅提供同步 `TaskGraph` 对象与异步 `TaskGraph` 对象传入 `benchmark_graph`

## 可能出现的问题

1. **环境变量依赖**：`REPORT_HOST` 等必须从 `.env` 加载，若未配置会导致 reporter 连接失败。
2. **总耗时长**：`benchmark_graph` 会运行 `len(stage_modes) × len(execution_modes)` 次完整图执行，含 I/O 延迟时总时间可达数分钟。

## 运行方式

```bash
python bench/bench_graph_mode.py
```

## 参数调整

### 单独运行某个测试场景

在 `bench/bench_graph_mode.py` 的 `main()` 中可选择只运行某个场景：

```python
if __name__ == "__main__":
    bench_graph_0()     # 运行 4 节点 DAG 混合场景（默认已注释）
    bench_graph_1()     # 当前启用：6 节点多层 DAG
    bench_graph_2()     # 当前启用：Splitter 吞吐量测试
```

### 调整输入规模

```python
# bench_graph_2 默认输入 range(10_000)，可减小以快速验证
# 在函数内部修改输入范围
inputs = range(1_000)  # 改为 1000 个任务，快速验证
```

### 修改 Worker 数

各场景的默认 worker 数在代码中可直接调整：

```python
# 在 bench_graph_0 内部
max_workers = 4   # 减少并发 Worker
```

修改后运行：

```bash
python bench/bench_graph_mode.py
```

## 基准结果（实测）

### 历史结果 - Windows 图模式对比（时间未记录）

> 环境：Windows，Python 3.10

#### `bench_graph_0` — 4 节点 DAG，CPU+I/O 混合，12 个任务（含异常边界）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |
| **process** | 9.88s | 4.99s | - |

注: `process` 模式已废除, 仅保留bench数据

- `thread` 与 `serial` stage_mode 在 CPU 密集型（斐波那契）场景下差异不大（GIL 限制）
- `execution_mode=thread` 和 `async` 均有 2-3x 加速（斐波那契计算释放 GIL 的部分 + sleep 阶段的 I/O 并发）
- `async` 与 `thread` 性能接近，async 在 I/O 密集场景下略有优势

#### `bench_graph_1` — 6 节点 DAG，I/O 密集（随机 sleep），10 个任务

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |
| **process** | 20.47s | 10.98s | - |

注: `process` 模式已废除, 仅保留bench数据

- 最优组合：`thread` + `async`（6.05s），比最差组合 `serial`+`serial`（54.25s）快 **9.0x**
- `async` 在 I/O 密集场景下优于 `thread`（协程切换开销小于线程切换）
- `thread`（线程布局）在 I/O 密集场景下显著优于 `serial`（单线程串行布局），各 stage 可并行启动

#### `bench_graph_2` — 4 节点 DAG（Splitter→A→[B,C]），纯计算，10,000 个任务

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` 最快**（1.09s）：纯计算无 I/O 等待，直接函数调用零开销
- `thread` 比 `serial` 慢 3.5x：线程池提交 + Future 同步的开销在微秒级任务上被放大
- `async` 比 `serial` 慢 10x：每个任务都要创建协程对象 + event loop 调度，但没有任何 I/O 等待点可以利用并发
- `stage_mode=thread` 同样增加了开销：stage 间的线程调度在纯计算场景下是纯负担
- **结论：纯计算密集型任务应使用 `serial` + `serial`，避免并发调度开销**

#### 总结

- `stage_mode=thread` 在 I/O 密集场景下是最优选择
- `execution_mode=async` 在 I/O 密集场景下表现最佳，`thread` 次之，`serial` 最慢
- **纯计算场景下 `serial` 最快**——`thread` 和 `async` 的调度开销在无 I/O 等待时无法被摊销，反而成为瓶颈
- `async` 需要 stage 的函数为 async 函数，因此需要分别提供 sync_graph 和 async_graph
- 总耗时包含：线程启动 + 任务执行 + 队列传输 + 终止信号传播

### 2026/06/16 - 本轮尝试重跑（未稳定完成）

> 环境：Windows，Reporter 服务指向 `127.0.0.1:5005`

- 本轮已按当前脚本入口尝试重跑 `bench_graph_mode.py`
- 命令在当前环境下长时间未返回稳定的完整耗时表，临时日志只落到单行表头
- 为避免把不完整数据写成正式 benchmark 记录，本次暂不追加新的耗时表，历史结果继续保留作参考

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部服务：Reporter 服务（可选）
