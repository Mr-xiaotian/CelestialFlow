# test_graph.py 测试说明

> 📅 最后更新日期: 2026/05/15

## 测试目标

验证 `TaskGraph` 及其子类（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskComplete`）在多种图结构下的正确性，包括：
- DAG 数据流的构建与执行
- 扇出（fan-out）、扇入（fan-in）、错误传播
- async 模式与 thread 模式下的图执行
- stage_mode x execution_mode 矩阵组合
- 图结构分析（DAG 检测、层级计算）
- 源节点自动推导
- 含环图的行为
- 运行时摘要统计

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestTaskGraphBasic` | 4 | 两节点 DAG、扇出、扇入、错误传播 |
| `TestTaskGraphAsync` | 5 | async 模式两节点、扇出、扇入、错误传播、async+thread stage_mode |
| `TestTaskGraphStructure` | 4 | Chain、Cross、Grid、Complete 结构 |
| `TestTaskGraphAnalysis` | 2 | DAG 检测、层级计算 |
| `TestTaskGraphSummary` | 1 | 摘要统计 |
| `TestStageExecutionMatrix` | 6 | serial/thread stage_mode x serial/thread/async execution_mode |
| `TestTaskGraphThread` | 6 | thread 模式两节点、扇出、扇入、错误传播、lambda、staged 调度 |
| `TestSourceStages` | 3 | 线性图 source、扇入 source、菱形图 source |
| `TestCyclicGraph` | 2 | 含环图 isDAG 检测、环内同层+尾巴层级 |

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

### 1. 线程模式下的超时风险
`TaskCross`、`TaskGrid`、`TaskComplete` 的默认 `stage_mode` 为 `"thread"`。若网格较大，线程启动和调度开销可能超过测试超时阈值。

**当前测试规模**：
- `test_cross_structure`：2×3 网格，4 个线程
- `test_grid_structure`：2×2 网格，4 个线程
- `test_complete_structure`：3 个节点，3 个线程

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

### `TestTaskGraphAsync` 详细用例说明

#### `test_graph_async_two_nodes`
- **目标**：async 模式下两节点 DAG 的数据流正确性。
- **断言**：`stage1` 和 `stage2` 各成功 3 个。

#### `test_graph_async_fan_out`
- **目标**：async 模式下扇出结构（一个上游到多个下游）。

#### `test_graph_async_fan_in`
- **目标**：async 模式下扇入结构（多个上游汇聚一个下游）。
- **断言**：merge 节点收到 4 个任务。

#### `test_graph_async_error_propagation`
- **目标**：async 模式下错误任务不阻断整体流程。

#### `test_graph_async_thread_stage_mode`
- **目标**：`stage_mode="thread"` + `execution_mode="async"` 组合下的正确执行。

### `TestStageExecutionMatrix` 详细用例说明

覆盖 `stage_mode`（serial/thread）x `execution_mode`（serial/thread/async）全部 6 种组合：

| 用例 | stage_mode | execution_mode |
|------|-----------|----------------|
| `test_serial_serial` | serial | serial |
| `test_serial_thread` | serial | thread |
| `test_serial_async` | serial | async |
| `test_thread_serial` | thread | serial |
| `test_thread_thread` | thread | thread |
| `test_thread_async` | thread | async |

每个用例均使用 5 个输入任务的两节点 DAG，验证两个 stage 各成功 5 个。

### `TestTaskGraphThread` 详细用例说明

#### `test_graph_thread_two_nodes`
- **目标**：thread stage_mode 下两节点 DAG 的数据流正确性。

#### `test_graph_thread_fan_out`
- **目标**：thread 模式下扇出结构。

#### `test_graph_thread_fan_in`
- **目标**：thread 模式下扇入结构。

#### `test_graph_thread_error_propagation`
- **目标**：thread 模式下错误任务不阻断流程。

#### `test_graph_thread_with_lambda`
- **目标**：thread 模式下支持 lambda 函数作为任务处理函数。

#### `test_graph_thread_staged_schedule`
- **目标**：thread 模式 + `schedule_mode="staged"` 下正常工作。

### `TestSourceStages` 详细用例说明

#### `test_source_stages_linear`
- **目标**：线性图（A → B → C）中 source 只有头节点 A。

#### `test_source_stages_fan_in`
- **目标**：两个入口汇入一点，source 为两个入口节点。

#### `test_source_stages_diamond`
- **目标**：菱形图 A → {B, C} → D 中 source 只有 A。

### `TestCyclicGraph` 详细用例说明

#### `test_cyclic_isDAG_false`
- **目标**：含环图（s1 → s2 → s3 → s1）的 `isDAG` 为 `False`。
- **注意**：使用 `put_termination_signal=True` 终止环。

#### `test_cyclic_layers`
- **目标**：环内节点（s1, s2, s3）同层，尾巴节点 s4 在环层级 + 1。

### 4. 任务函数的要求
所有测试的任务函数和参数使用顶层函数和基础类型，确保兼容性。

### 5. 线程安全
当前测试中所有线程创建均通过 `TaskGraph.start_graph()` 内部管理，无需额外保护。

## 运行方式

```bash
# 全部执行
pytest tests/test_graph.py -v

# 仅结构测试（最耗时，含多线程）
pytest tests/test_graph.py::TestTaskGraphStructure -v

# 仅分析测试（最快，无任务执行）
pytest tests/test_graph.py::TestTaskGraphAnalysis -v
```

## 性能参考

| 测试 | 耗时（Windows / i5） |
|------|---------------------|
| `TestTaskGraphBasic` | ~2s |
| `TestTaskGraphAsync` | ~3s |
| `TestTaskGraphStructure` | ~5s |
| `TestTaskGraphAnalysis` | ~1s |
| `TestTaskGraphSummary` | ~1s |
| `TestStageExecutionMatrix` | ~5s |
| `TestTaskGraphThread` | ~4s |
| `TestSourceStages` | ~2s |
| `TestCyclicGraph` | ~2s |

## 相关文件

- `src/celestialflow/graph/core_graph.py`：`TaskGraph` 实现
- `src/celestialflow/graph/core_structure.py`：图结构子类
- `tests/demo_structure.py`：更复杂的图结构演示（含循环图、多层网络）
