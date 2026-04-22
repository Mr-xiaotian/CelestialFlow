# test_graph.py 测试说明

## 测试目标

验证 `TaskGraph` 及其子类（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`）在多种图结构下的正确性，包括：
- DAG 数据流的构建与执行
- 扇出（fan-out）、扇入（fan-in）、错误传播
- 图结构分析（DAG 检测、层级计算）
- 运行时摘要统计

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskGraphBasic` | 4 | 两节点 DAG、扇出、扇入、错误传播 |
| `TestTaskGraphStructure` | 4 | Chain、Cross、Grid、Complete 结构 |
| `TestTaskGraphAnalysis` | 2 | DAG 检测、层级计算 |
| `TestTaskGraphSummary` | 1 | 摘要统计 |

### 关键用例详解

#### `test_graph_dag_two_nodes`
- **目标**：最简 DAG（A → B）的数据流正确性。
- **断言**：`stage1` 成功 3 个，`stage2` 成功 3 个（结果正确传递）。

#### `test_graph_fan_out`
- **目标**：一个上游节点分发到多个下游节点。
- **断言**：source 2 个，sink_a 2 个，sink_b 2 个。

#### `test_graph_fan_in`
- **目标**：多个上游节点汇聚到一个下游节点。
- **断言**：merge 节点收到 4 个任务（2 + 2）。

#### `test_graph_error_propagation`
- **目标**：错误任务不阻断整体流程，且不会传递到下游。
- **设计**：`stage1` 处理 `[1, 50, 2]`，其中 `50` 触发 `ValueError`。
- **断言**：`stage1` 成功 2、失败 1；`stage2` 仅收到 2 个成功任务。

#### `test_complete_structure`
- **目标**：完全图（非 DAG）的基本启动与结构检测。
- **注意**：完全图自动注入终止信号会触发 `RuntimeWarning`，节点可能提前关闭。测试仅验证 `isDAG == False` 和每个节点至少处理了自身输入。

#### `test_layer_computation`
- **目标**：DAG 的层级（topological level）计算正确。
- **设计**：A → B → C 三层链。
- **断言**：A 在第 0 层，B 在第 1 层，C 在第 2 层。

#### `test_graph_summary_counts`
- **目标**：`collect_runtime_snapshot()` 生成的摘要统计准确。
- **注意**：测试中未启用 `TaskReporter`，需**手动调用** `collect_runtime_snapshot()` 才能生成摘要。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `celestialflow` | `TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`、`TaskStage` |

## 可能的问题与注意事项

### 1. 多进程模式下的超时风险
`TaskCross`、`TaskGrid`、`TaskComplete` 的默认 `stage_mode` 为 `"process"`。在 Windows 上，每个 `multiprocessing.Process` 的启动开销约为 100-300ms。若网格较大（如 4×4），总启动时间可能超过测试超时阈值。

**当前测试规模**：
- `test_cross_structure`：2×3 网格，4 个进程
- `test_grid_structure`：2×2 网格，4 个进程
- `test_complete_structure`：3 个节点，3 个进程

以上规模在 180 秒超时内可稳定通过。

### 2. 非 DAG 图的终止信号行为
`TaskComplete`、`TaskLoop`、`TaskWheel` 等含环结构在 `put_termination_signal=True` 时会触发框架警告：
```
RuntimeWarning: Early injection of termination signals in a non-DAG graph ...
```

这是因为 eager 模式下节点可能在收到终止信号后立即关闭，而来自其他节点的后续任务可能还在队列中。当前测试已调整断言为 `>= 1` 而非精确值，以适配此行为。

**建议**：若需精确测试有环图的任务计数，应：
1. 使用 `put_termination_signal=False`
2. 通过 Web 接口或外部注入终止信号
3. 在 staged 模式下运行（有环图不支持 staged）

### 3. `collect_runtime_snapshot` 的手动调用
`get_graph_summary()` 返回的数据来自上一次 `collect_runtime_snapshot()` 的快照。在正式运行中，`TaskReporter` 会周期性自动调用；但在单元测试中（未启用 reporter），必须手动调用。

遗漏此调用会导致 `get_graph_summary()` 返回空字典或旧数据。

### 4. `stage_mode="process"` 与 Pickle
所有使用 `stage_mode="process"` 的测试，其任务函数和参数必须可被 pickle。当前测试使用的均为顶层函数和基础类型，无此问题。

### 5. Windows 的进程 spawn 开销
Windows 默认使用 `spawn` 方式创建进程（Linux/macOS 为 `fork`）。`spawn` 会重新导入主模块，若 `if __name__ == "__main__":` 保护不当，可能导致递归创建进程。

**当前测试**：所有进程创建均通过 `TaskGraph.start_graph()` 内部管理，无需额外保护。

## 运行方式

```bash
# 全部执行
pytest tests/test_graph.py -v

# 仅结构测试（最耗时，含多进程）
pytest tests/test_graph.py::TestTaskGraphStructure -v

# 仅分析测试（最快，无任务执行）
pytest tests/test_graph.py::TestTaskGraphAnalysis -v
```

## 性能参考

| 测试 | 耗时（Windows / i5） |
|------|---------------------|
| `TestTaskGraphBasic` | ~2s |
| `TestTaskGraphStructure` | ~5s |
| `TestTaskGraphAnalysis` | ~1s |
| `TestTaskGraphSummary` | ~1s |

## 相关文件

- `src/celestialflow/graph/core_graph.py`：`TaskGraph` 实现
- `src/celestialflow/graph/core_structure.py`：图结构子类
- `tests/demo_structure.py`：更复杂的图结构演示（含循环图、多层网络）
