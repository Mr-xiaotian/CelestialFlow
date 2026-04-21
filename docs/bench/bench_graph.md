# bench_graph.py 基准测试说明

## 目标

对比不同 `stage_mode`（`serial` / `process`）和 `execution_mode`（`serial` / `thread`）组合下，复杂 DAG 的任务图执行性能。使用框架内置的 `benchmark_graph` 工具进行矩阵式对比。

## 测试内容

### `bench_graph_0`
- **结构**：4 节点 DAG（`stage1 → [stage2, stage3] → stage4`）
- **任务混合**：CPU 密集型（斐波那契）、I/O 密集型（sleep）、纯计算（除二、平方）
- **输入**：`range(25, 32) + [0, 27, None, 0, ""]`（含异常边界）
- **启用服务**：Reporter、CelestialTree

### `bench_graph_1`
- **结构**：6 节点多层 DAG（A → [B, C] → [D, E] → F）
- **任务**：随机 0-2 秒睡眠（模拟不均匀负载）
- **输入**：`range(10)`
- **启用服务**：Reporter、CelestialTree

## 关键配置

- `stage_modes = ["serial", "process"]`
- `execution_modes = ["serial", "thread"]`
- 共 **4 种组合**，每种都会完整跑一遍图

## 可能出现的问题

1. **环境变量依赖**：`REPORT_HOST`、`CTREE_HOST` 等必须从 `.env` 加载，若未配置会导致 reporter/ctree 连接失败。
2. **CelestialTree 未启动**：若 `set_ctree(True)` 但服务未运行，`start_graph()` 会抛出连接异常。
3. **Windows 多进程开销**：`stage_mode="process"` 时每个 stage 启动独立进程，4 个 stage 的 DAG 在 Windows 上启动时间可能超过实际任务执行时间。
4. **总耗时长**：`benchmark_graph` 会运行 `len(stage_modes) × len(execution_modes)` 次完整图执行，含 I/O 延迟时总时间可达数分钟。

## 运行方式

```bash
python bench/bench_graph.py
```

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部服务：CelestialTree（可选）、Reporter 服务（可选）
