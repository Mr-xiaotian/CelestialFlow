# bench_gil_vs_nogil.py 基准测试说明

> 📅 最后更新日期: 2026/06/18

## 目标

对比 `CelestialFlow` 在 Python 3.14 标准版（启用 GIL）与 free-threading 版（禁用 GIL）下的运行差异，重点观察以下两类能力：

- `TaskExecutor` 在线程执行 CPU 任务时的吞吐变化
- `TaskGraph` 在线程流水线下的整体加速效果

这个 benchmark 不会在一个进程里自动拉起两个 Python 环境，而是只测试**当前解释器**。因此需要分别在 GIL 和 No-GIL 环境中各运行一次，再手动对比结果。

## 测试内容

脚本文件：`bench/bench_gil_vs_nogil.py`

| Workload | 说明 |
|------|------|
| `executor_cpu_serial` | `TaskExecutor` 串行执行 CPU 密集任务 |
| `executor_cpu_thread` | `TaskExecutor` 线程执行 CPU 密集任务 |
| `graph_cpu_pipeline_serial` | 3-stage `TaskGraph` 串行 CPU 流水线 |
| `graph_cpu_pipeline_thread` | 3-stage `TaskGraph` 线程 CPU 流水线 |
| `graph_io_pipeline_thread` | 3-stage `TaskGraph` 线程 I/O 流水线 |

### 测试负载设计

- **CPU 任务**：执行纯 Python 整数循环和哈希式混合运算，尽量压中 Python 字节码执行开销
- **I/O 任务**：`time.sleep()` 模拟阻塞等待
- **图结构**：固定为 3 个 stage 的简单串联流水线，避免图拓扑差异干扰结果
- **日志级别**：统一使用 `CRITICAL`，尽量减小日志打印对 benchmark 的污染
- **重复次数**：默认每个 workload 运行 3 次，并统计平均值 / 最小值 / 最大值

## 关键配置

默认参数如下：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `repeats` | `3` | 每个 workload 的重复次数 |
| `workers` | `0` | 自动取 `min(os.cpu_count(), 16)` |
| `cpu_tasks` | `128` | `TaskExecutor` CPU 测试任务数 |
| `cpu_loops` | `120000` | 单个 CPU 任务的循环强度 |
| `pipeline_tasks` | `96` | `TaskGraph` 流水线任务数 |
| `pipeline_loops` | `60000` | 流水线 CPU 任务的循环强度 |
| `io_tasks` | `96` | I/O 流水线任务数 |
| `io_sleep_ms` | `10.0` | 每个 I/O 任务的 sleep 时长（毫秒） |

## 运行方式

因为脚本只测试当前解释器，请分别在两套 Python 3.14 环境中运行。

### 在 GIL 环境中运行

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_gil_result.json
```

### 在 No-GIL 环境中运行

```bash
python bench/bench_gil_vs_nogil.py --json-out bench_nogil_result.json
```

如果你本地像示例一样维护了两套 `uv` 虚拟环境，也可以显式调用：

```powershell
.\gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_gil_result.json
.\no-gil\.venv\Scripts\python.exe .\bench\bench_gil_vs_nogil.py --json-out .\bench_nogil_result.json
```

## 参数调整

### 调整 worker 数

```bash
python bench/bench_gil_vs_nogil.py --workers 8
```

### 缩小任务规模做快速验证

```bash
python bench/bench_gil_vs_nogil.py \
  --repeats 1 \
  --workers 4 \
  --cpu-tasks 16 \
  --cpu-loops 20000 \
  --pipeline-tasks 12 \
  --pipeline-loops 10000 \
  --io-tasks 12 \
  --io-sleep-ms 2
```

### 增大 CPU 压力

```bash
python bench/bench_gil_vs_nogil.py --cpu-loops 200000 --pipeline-loops 100000
```

## 可能出现的问题

1. **必须分开跑两次**：脚本不会自动切换 Python 环境，比较结果时需要自行收集两份输出。
2. **首次运行会写入 fallback sqlite**：`TaskExecutor` / `TaskGraph` 在运行时会创建 `fallback/` 目录，因此脚本会先把工作目录切到仓库根目录，避免临时路径或权限限制。
3. **不要混用不同参数结果**：若 GIL 与 No-GIL 两次运行时参数不一致，结果不具可比性。
4. **CPU 频率波动会影响结果**：Windows 下后台负载、温控与电源策略会让单次结果抖动，因此默认重复 3 次取均值。

## 基准结果（实测）

### 2026/06/18 - Windows 11 / Python 3.14.3 / 8 workers

> 本轮使用参数：
> `repeats=3, workers=8, cpu_tasks=96, cpu_loops=100000, pipeline_tasks=72, pipeline_loops=50000, io_tasks=72, io_sleep_ms=10`

| Workload | GIL Mean | No-GIL Mean | No-GIL 相对表现 |
|------|-----------|--------------|------------------|
| `executor_cpu_serial` | 1.1148s | 1.0836s | **1.03x** |
| `executor_cpu_thread` | 1.1191s | 0.2131s | **5.25x** |
| `graph_cpu_pipeline_serial` | 1.3526s | 1.2443s | **1.09x** |
| `graph_cpu_pipeline_thread` | 1.4777s | 0.1957s | **7.55x** |
| `graph_io_pipeline_thread` | 0.1514s | 0.1322s | **1.15x** |

其中：

```text
No-GIL 相对表现 = GIL 平均耗时 / No-GIL 平均耗时
```

数值大于 `1.00x` 时表示 No-GIL 更快。

### 结果解读

- **串行 CPU 模式差异不大**：`executor_cpu_serial` 和 `graph_cpu_pipeline_serial` 仅有约 `3% ~ 9%` 的提升，说明 No-GIL 并不会神奇加速单线程纯 Python 执行。
- **线程 CPU 模式提升显著**：`executor_cpu_thread` 达到约 **5.25x**，`graph_cpu_pipeline_thread` 达到约 **7.55x**。
- **图级线程流水线提升更大**：相比单执行器线程模式，`TaskGraph` 的线程流水线更充分地利用了 free-threading 带来的并行能力。
- **I/O 模式有提升但不是主角**：`graph_io_pipeline_thread` 仅领先约 **15%**，符合 I/O 等待本就能在 GIL 下较好并发的直觉。

## 适用场景

这个 benchmark 适合回答以下问题：

- 如果把 `CelestialFlow` 部署到 Python 3.14 No-GIL 环境，线程模式能提升多少？
- `TaskExecutor` 和 `TaskGraph` 哪一层从 No-GIL 中获益更明显？
- 当前工作负载更接近 CPU 线程型还是 I/O 型？

如果你的目标是：

- **比较 async / thread / serial 三种 execution mode**：优先看 `bench_execution_mode.py`
- **比较不同 graph mode / DAG 拓扑组合**：优先看 `bench_graph_mode.py`
- **专门比较 Python 解释器的 GIL 与 No-GIL 差异**：使用本文件

## 依赖

- `celestialflow`
- Python 3.14 标准版（GIL）
- Python 3.14 free-threading 版（No-GIL）
