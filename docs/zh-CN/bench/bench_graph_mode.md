# bench_graph_mode.py 基准测试说明

> 📅 最后更新日期: 2026/05/09

## 目标

对比不同 `stage_mode`（`serial` / `thread`）和 `execution_mode`（`serial` / `thread`）组合下，复杂 DAG 的任务图执行性能。使用框架内置的 `benchmark_graph` 工具进行矩阵式对比。

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

- `stage_modes = ["serial", "thread"]`
- `execution_modes = ["serial", "thread"]`
- 共 **4 种组合**，每种都会完整跑一遍图

## 可能出现的问题

1. **环境变量依赖**：`REPORT_HOST`、`CTREE_HOST` 等必须从 `.env` 加载，若未配置会导致 reporter/ctree 连接失败。
2. **CelestialTree 未启动**：若 `set_ctree(True)` 但服务未运行，`start_graph()` 会抛出连接异常。
3. **总耗时长**：`benchmark_graph` 会运行 `len(stage_modes) × len(execution_modes)` 次完整图执行，含 I/O 延迟时总时间可达数分钟。

## 运行方式

```bash
python bench/bench_graph_mode.py
```

## 基准结果（实测）

> 环境：Windows，Python 3.10

### `bench_graph_0` — 4 节点 DAG，CPU+I/O 混合，11 个任务（含异常边界）

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 7.70s | 2.82s |
| **thread** | 7.12s | 2.63s |

- `thread` 与 `serial` stage_mode 在 CPU 密集型（斐波那契）场景下差异不大（GIL 限制）
- `execution_mode=thread` 仍有 2-3x 加速（斐波那契计算释放 GIL 的部分 + sleep 阶段的 I/O 并发）

### `bench_graph_1` — 6 节点 DAG，I/O 密集（随机 sleep），10 个任务

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 61.20s | 17.08s |
| **thread** | 17.07s | 7.07s |

- 最优组合：`thread` + `thread`（7.07s），比最差组合 `serial`+`serial`（61.20s）快 **8.7x**
- `thread`（线程布局）在 I/O 密集场景下显著优于 `serial`（单线程串行布局），各 stage 可并行启动

### 总结

- `stage_mode=thread` 在 I/O 密集场景下是最优选择
- `execution_mode=thread` 在所有场景下都优于 `serial`
- 总耗时包含：线程启动 + 任务执行 + 队列传输 + 终止信号传播

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部服务：CelestialTree（可选）、Reporter 服务（可选）
