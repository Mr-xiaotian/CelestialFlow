# demo_structure.py 演示说明

## 目标

演示 `core_structure.py` 中预定义的多种图结构（DAG 与有环图），展示 CelestialFlow 在链式、交叉、网格、循环、轮状、完全图等多种拓扑下的构建与运行方式。

## 演示结构

### DAG（有向无环图）

| 函数 | 结构 | 说明 |
|------|------|------|
| `test_chain` | TaskChain | 5 节点线性链，进程模式 |
| `test_forest` | TaskGraph | 两棵独立的树状 DAG 并存 |
| `test_cross` | TaskCross | 3 层交叉结构（3→1→3） |
| `test_network` | TaskCross | 多层多分支网络（2→3→1） |
| `test_star` | TaskCross | 中心节点指向多个边缘节点 |
| `test_fanin` | TaskCross | 多个源节点汇入一个合并节点 |
| `test_grid` | TaskGrid | 4×4 进程网格，staged 调度 |

### 有环图

| 函数 | 结构 | 说明 |
|------|------|------|
| `test_loop` | TaskLoop | 3 节点闭环，自锁结构 |
| `test_wheel` | TaskWheel | 中心节点 + 4 个环节点 |
| `test_complete` | TaskComplete | 3 节点完全图，两两相连 |

## 关键配置

- DAG 结构：`stage_mode="process"`，`execution_mode="thread"`
- `test_grid`：使用 `staged` 调度模式（逐层执行）
- 有环图：`put_termination_signal=False`（建议外部控制停止）
- 所有演示均启用 `Reporter` 和 `CelestialTree`

## 可能出现的问题

1. **有环图不会自动停止**：`test_loop`、`test_complete` 等使用 `put_termination_signal=False`，运行后会持续循环直到手动终止进程。
2. **进程启动开销**：大量 `stage_mode="process"` 的节点在 Windows 上启动缓慢，`test_grid`（16 个进程）可能需要数十秒初始化。
3. **sleep 延迟累积**：`add_one_sleep` 含 1 秒 sleep，20 个任务 × 多节点 = 长总耗时。
4. **无断言**：仅验证框架能启动和运行，不检查结果数值。

## 运行方式

```bash
python demo/demo_structure.py
```

## 依赖

- `celestialflow`（`TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`、`TaskStage`）
- `demo_utils`
- `python-dotenv`
- 外部服务：CelestialTree（可选）、Reporter（可选）
