# demo_structure.py 演示说明

> 📅 最后更新日期: 2026/05/09

## 目标

演示 `core_structure.py` 中预定义的多种图结构（DAG 与有环图），展示 CelestialFlow 在链式、交叉、网格、循环、轮状、完全图等多种拓扑下的构建与运行方式。

## 演示结构

### DAG（有向无环图）

| 函数 | 结构 | 说明 |
|------|------|------|
| `demo_chain` | TaskChain | 5 节点线性链，线程模式 |
| `demo_forest` | TaskGraph | 两棵独立的树状 DAG 并存 |
| `demo_cross` | TaskCross | 3 层交叉结构（3→1→3） |
| `demo_network` | TaskCross | 多层多分支网络（2→3→1） |
| `demo_star` | TaskCross | 中心节点指向多个边缘节点 |
| `demo_fanin` | TaskCross | 多个源节点汇入一个合并节点 |
| `demo_grid` | TaskGrid | 4×4 线程网格，staged 调度 |

### 有环图

| 函数 | 结构 | 说明 |
|------|------|------|
| `demo_loop` | TaskLoop | 3 节点闭环，自锁结构 |
| `demo_wheel` | TaskWheel | 中心节点 + 4 个环节点 |
| `demo_complete` | TaskComplete | 3 节点完全图，两两相连 |

## 关键配置

- DAG 结构：`stage_mode="thread"`，`execution_mode="thread"`
- `demo_grid`：使用 `staged` 调度模式（逐层执行）
- 有环图：`put_termination_signal=False`（建议外部控制停止）
- 所有演示均启用 `Reporter` 和 `CelestialTree`

## 可能出现的问题

1. **有环图不会自动停止**：`demo_loop`、`demo_complete` 等使用 `put_termination_signal=False`，运行后会持续循环直到手动终止进程。
2. **sleep 延迟累积**：`add_one_sleep` 含 1 秒 sleep，20 个任务 × 多节点 = 长总耗时。
3. **无断言**：仅验证框架能启动和运行，不检查结果数值。

## 运行方式

```bash
python demo/demo_structure.py
```

## 依赖

- `celestialflow`（`TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`、`TaskStage`）
- `demo_utils`
- `python-dotenv`
- 外部服务：CelestialTree（可选）、Reporter（可选）
