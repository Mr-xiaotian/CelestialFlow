# bench_graph_mode.py 基准测试说明

> 📅 最后更新日期: 2026/08/17

## 目标

对比不同 `graph_mode`（`serial` / `thread` / `async`）和 `execution_mode`（`serial` / `thread` / `async`）组合下，复杂 DAG 的任务图执行性能。使用框架内置的 `benchmark_graph` 工具进行 3×3 矩阵式对比。

## 测试内容

### `bench_graph_0`
- **结构**：4 节点 DAG，`stage1 → stage2 → stage4`，`stage1 → stage3`（stage3 为不汇入 stage4 的独立分支）
- **任务混合**：CPU 密集型（斐波那契）、I/O 密集型（sleep）、纯计算（除二、平方）
- **输入**：`range(25, 32) + [0, 27, None, 0, ""]`（含异常边界）
- **重试设置**：`stage1`、`stage2` 对 `ValueError` 启用 `max_retries=1`
- **Reporter**：默认关闭（代码中已注释，可通过取消注释启用）

### `bench_graph_1`
- **结构**：6 节点多层 DAG（A → [B, C]；B → [D, E]；C → E；D → F）
- **任务**：随机 0-2 秒睡眠（模拟不均匀负载）
- **输入**：`range(10)`
- **Reporter**：默认关闭（代码中已注释，可通过取消注释启用）

### `bench_graph_2`
- **结构**：4 节点 DAG（Splitter → A → [B, C]），使用 `TaskSplitter` 展开输入
- **任务**：纯计算（加一、乘二），测试框架调度吞吐上限
- **输入**：`range(10_000)`（经 Splitter 展开为 10,000 个独立任务）

## 关键配置

- `benchmark_graph` 内部会遍历 `graph_mode`（`serial` / `thread` / `async`）和 `execution_mode`（`serial` / `thread` / `async`）的组合，共 **9 种组合**
- 同步节点模板通过 `graph` 传入，异步节点模板通过 `async_graph` 传入；`benchmark_graph` 会按列选择合适的模板
- 当组合为 `serial/thread + async` 时，基准函数会在后台线程中调用同步图入口，以避免与自身事件循环冲突

## 可能出现的问题

1. **环境变量依赖**：`REPORT_HOST` 等必须从 `.env` 加载，若未配置会导致 reporter 连接失败。
2. **总耗时长**：`benchmark_graph` 会运行 `len(graph_modes) × len(execution_modes)` 次完整图执行，含 I/O 延迟时总时间可达数分钟。

## 运行方式

```bash
python bench/bench_graph_mode.py
```

## 参数调整

### 单独运行某个测试场景

> `benchmark_graph` 已改为 `async` 函数，`bench_graph_*` 均为 `async def`，需通过 `main_async()` 或 `asyncio.run()` 调用。

在 `bench/bench_graph_mode.py` 的 `main_async()` 中可选择只运行某个场景：

```python
async def main_async() -> None:
    # await bench_graph_0()
    # await bench_graph_1()
    await bench_graph_2()

if __name__ == "__main__":
    asyncio.run(main_async())
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

### 2026/08/05 — `start_graph_async` 重构后重跑

> 环境：macOS，Python 3.14，Reporter **已关闭**（避免 HTTP timeout 干扰耗时）
> 变更：`benchmark_graph` 改为 `async` 函数，`async` execution mode 使用 `start_graph_async` 而非 `start_graph`

#### `bench_graph_0` — 4 节点 DAG，CPU+I/O 混合，12 个任务（含异常边界）

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.17s | 1.17s | 1.16s |
| **thread** | 8.06s | 1.17s | 1.17s |
| **async**  | 8.05s | 1.17s | 1.15s |

- 三行差距极小，说明该场景的主导因素仍是节点内部的并发方式，而不是图层面的启动方式
- `execution_mode=thread` 与 `async` 都把总耗时压到了约 1.15s–1.17s，相比 `serial` 列约有 **7x** 提升
- `graph_mode="async"` 没有额外带来明显收益，说明在这个 4 节点混合 DAG 中，图调度成本已被任务执行时间掩盖

#### `bench_graph_1` — 6 节点 DAG，I/O 密集（随机 sleep），10 个任务

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 71.19s | 12.03s | 13.03s |
| **thread** | 21.05s | 7.03s  | 6.02s  |
| **async**  | 30.07s | 7.02s  | 6.01s  |

- 最优组合是 `async + async`（6.01s）与 `thread + async`（6.02s），两者几乎持平
- 图层面从 `serial` 提升到 `thread/async` 的收益非常明显：即使 `execution_mode=serial`，也能从 71.19s 降到 21.05s 或 30.07s
- `execution_mode=thread` 和 `async` 在 `thread/async graph_mode` 下都显著优于纯串行，说明该场景主要受益于 I/O 重叠与多节点并发启动

#### `bench_graph_2` — 4 节点 DAG（Splitter→A→[B,C]），纯计算，10,000 个任务

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.10s | 1.63s | 2.10s |
| **thread** | 1.10s | 1.56s | 2.41s |
| **async**  | 1.11s | 1.56s | 1.92s |

- `serial + serial` 仍然是最优解，说明纯计算型小任务场景下，直接函数调用开销最低
- `execution_mode=thread` 会引入线程池提交与同步开销，因此整体慢于 `serial`
- `execution_mode=async` 最慢，原因仍然是协程创建与调度成本无法被 I/O 等待摊销
- 该场景含 `TaskSplitter`，它始终固定为 `execution_mode="serial"`；因此这组数据是“以 Splitter 为串行入口的混合模式” benchmark，而不是所有节点都严格切到同一种 execution mode

#### 本轮总结

- `benchmark_graph` 现在已经能直接输出完整的 `3 × 3` 组合矩阵
- 对 I/O 密集 DAG，`graph_mode=thread/async` 搭配 `execution_mode=thread/async` 的收益最明显
- 对混合型 DAG，节点内部并发方式比图层面的启动方式更主导结果
- 对纯计算微任务，`serial + serial` 依然最稳妥，额外并发层通常只会放大调度开销

> 本轮数据与 2026/08/05 的结果不可直接逐列比较：一方面运行环境从 Windows 切换到了 macOS；另一方面矩阵已从原先不完整的组合扩展为完整 9 宫格，`async` 列的语义也已修正。

### 2026/08/05 — `start_graph_async` 重构后重跑

> 环境：Windows，Python 3.14，Reporter **已关闭**（避免 HTTP timeout 干扰耗时）
> 变更：`benchmark_graph` 改为 `async` 函数，`async` execution mode 使用 `start_graph_async` 而非 `start_graph`

#### `bench_graph_0` — 4 节点 DAG，CPU+I/O 混合，12 个任务（含异常边界）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.36s | 1.38s | 1.39s |
| **thread** | 8.11s | 1.39s | 1.38s |

- I/O 部分（`sleep_1`）占比不高时，`thread` 和 `async` 仍能带来约 **6x** 加速
- `stage_mode` 在该场景下影响不大（thread 布局的开销被任务执行时间掩盖）

#### `bench_graph_1` — 6 节点 DAG，I/O 密集（随机 sleep），10 个任务

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 69.04s | 12.03s | 6.05s |
| **thread** | 19.02s | 6.02s | 8.06s |

- 最优组合：`serial`+`async`（6.05s），比最差 `serial`+`serial`（69.04s）快 **11.4x**
- `stage_mode=thread` + `execution_mode=async`（8.06s）反而慢于 `serial`+`async`（6.05s），原因是 thread stage 间的线程切换 + async 协程调度产生了双重开销
- `execution_mode=async` 在 I/O 密集场景下首次正确生效（之前误走同步路径），优势明显

#### `bench_graph_2` — 4 节点 DAG（Splitter→A→[B,C]），纯计算，10,000 个任务

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 2.65s | 3.18s | 6.05s |
| **thread** | 2.55s | 4.64s | 5.50s |

- `serial`+`serial`（2.65s）最快，纯计算场景结论不变
- `async` 因无 I/O 等待，协程调度开销导致减速约 **2.3x**
- 整体比旧版（带 Reporter）快了约 3x，验证 Reporter 的 HTTP timeout 在前轮数据中贡献了大量额外耗时

> **Reporter 影响说明**：前一轮数据中 Reporter 服务未运行，后台线程每 5 秒一次 HTTP 请求等待 timeout，显著拉长了整体耗时。本轮全部关闭 Reporter 后，数据更准确地反映框架本身的调度性能。
>
> 旧版（2026/07/16 前）`execution_mode="async"` 时实际走的是 `start_graph` 同步路径（`start_stage` 内部调用 `asyncio.run`），新版通过 `start_graph_async` 正确走协程路径，历史数据不再可比。

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部服务：Reporter 服务（可选）
