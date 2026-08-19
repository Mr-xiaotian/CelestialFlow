# 特定图结构测试 (test_structure.py)

> 📅 最后更新日期: 2026/08/19

## 作用
验证 `TaskLoop` 和 `TaskWheel` 两种预定义含环图结构的专用分析能力，以及各类预定义图结构（`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`）的输入校验，确保空/非法输入不会导致静默构造或崩溃。

## 核心测试对象
- `TaskLoop`: 简单的闭环任务链。
- `TaskWheel`: 中心扩散并带环的轮式结构。
- `TaskChain`, `TaskCross`, `TaskGrid`, `TaskComplete`: 预定义图结构的空/非法输入校验。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 |
|--------|--------|---------|
| `TestTaskLoop` | 2 | isDAG 识别为 False、环内节点同层、源节点推导返回一个代表点 |
| `TestTaskWheel` | 2 | Center 在第 0 层、Ring 在第 1 层、源节点仅返回 Center |
| `TestStructureValidation` | 10 | 空 stages/空 layers/空网格/首行为空/行长度不一致/单节点 Complete/各结构空输入校验 |
| **合计** | **14** | |

## 关键测试流程

### TaskLoop 分析
- 验证 `isDAG` 被正确识别为 `False`。
- 验证环内所有节点都被分配到同一个逻辑层级。
- 验证源节点推导能从环中选取一个代表点作为注入点。

### TaskWheel 分析
- 验证中心节点（Center）处于第 0 层，而外环节点（Ring）处于第 1 层。
- 验证 `get_source_stages` 仅返回 Center 节点，确保任务从中心注入。

### 结构输入校验 (`TestStructureValidation`)
覆盖全部 6 种预定义图结构的空/非法输入边界：

| 用例 | 验证点 |
|------|--------|
| `test_chain_empty_stages_raises` | `TaskChain` 空 stages 抛出 `InvalidStructureError` |
| `test_cross_empty_layers_raises` | `TaskCross` 空 layers 抛出 `InvalidStructureError` |
| `test_cross_empty_layer_raises` | `TaskCross` 包含空层抛出 `InvalidStructureError` |
| `test_grid_empty_raises` | `TaskGrid` 空网格抛出 `InvalidStructureError` |
| `test_grid_empty_row_raises` | `TaskGrid` 首行为空抛出 `InvalidStructureError` |
| `test_grid_ragged_rows_raises` | `TaskGrid` 行长度不一致抛出 `InvalidStructureError` |
| `test_loop_empty_stages_raises` | `TaskLoop` 空 stages 抛出 `InvalidStructureError` |
| `test_wheel_empty_ring_raises` | `TaskWheel` 空 ring 抛出 `InvalidStructureError` |
| `test_complete_single_node_raises` | `TaskComplete` 单节点抛出 `InvalidStructureError` |
| `test_complete_empty_stages_raises` | `TaskComplete` 空 stages 抛出 `InvalidStructureError` |

## 测试重点
- **非 DAG 识别**: 确保含环结构不会被错误地当作 DAG 处理。
- **层级一致性**: 验证在存在循环依赖时，逻辑层级的划分依然符合物理直觉。
- **源节点特化**: 针对特定结构优化的源节点查找逻辑。
- **边界校验**: 确保所有预定义图结构均严格拒绝空/非法输入，而非静默构造空图。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_structure.py -v

# 仅运行 TaskLoop 测试
pytest tests/graph/test_structure.py::TestTaskLoop -v

# 仅运行 TaskWheel 测试
pytest tests/graph/test_structure.py::TestTaskWheel -v

# 仅运行输入校验测试
pytest tests/graph/test_structure.py::TestStructureValidation -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestTaskLoop` | ~1s（含图启动与终止） |
| `TestTaskWheel` | ~1s |
| `TestStructureValidation` | < 0.1s（纯构造校验） |

## 重要细节
- 使用 `start()` 方法启动测试，并配合 `put_tasks(..., if_put_signal=True)` 注入终止信号。
- `TaskWheel` 通过 `set_graph_mode()` 与 `set_stage_execution_mode()` 配置后调用 `get_graph_analysis()` 进行分析。
- 测试重点在于"分析结果"（analysis dict）而非"执行结果"。
- 输入校验测试均为纯构造操作，不涉及图启动。

## 注意事项
- 本测试侧重于 `TaskGraph` 子类的特化行为。
- 相关实现位于 `src/celestialflow/graph/core_structure.py`。
