# 图分析工具测试 (test_order_graph.py)

> 📅 最后更新日期: 2026/08/26

## 作用
验证 `celestialflow.graph.util_order_graph` 中的基础图分析能力，包括 `OrderGraph` 构建、层级计算（`compute_node_levels`）、源节点查找（`source_nodes`）、SCC 划分（`tarjan_scc`），以及深度超过 Python 默认递归上限（约 1000）时的迭代算法回归。

## 核心测试对象
- `OrderGraph.from_edges` / `add_node` / `add_edge` / `successors`: 构造与查询有序图结构。
- `compute_node_levels`: 计算图中各节点的逻辑层级（SCC 内共享层级）。
- `source_nodes`: 查找图的入口节点（源节点，SCC 只返回一个代表点）。
- `tarjan_scc`: 强连通分量划分（迭代实现）。
- `DEEP = 5000`: 超过 Python 默认递归上限的深链/深环规模，用于回归迭代版 `tarjan_scc`。

## 测试覆盖矩阵

| 测试类 | 用例数 | 覆盖目标 | 关键断言 |
|--------|--------|---------|---------|
| `TestBuildOrderGraph` | 3 | 线性链 / 含环 / 孤立节点的图构建 | 节点数、边总数、`successors` 邻接方向正确 |
| `TestComputeNodeLevels` | 5 | 线性 DAG、扇出 DAG、简单环、带尾巴的环、不连通图 | 层级递增、B/C 同层、环内共享层级、尾巴比环高一层、各连通分量独立从 0 开始 |
| `TestFindSourceNodes` | 4 | 线性 DAG、多源、纯环、轮状拓扑 | 入度为 0 的源节点；纯环 SCC 返回一个代表点；Center 是唯一 source |
| `TestDeepGraphRegression` | 3 | 5000 节点深链 / 深环 / 经 TaskGraph 全链路建图 | 深链 SCC 全单点、无 RecursionError；深环收敛为单一 SCC；`get_structure_graph` / `get_source_names` / `get_graph_analysis` 正常 |
| **合计** | **15** | | |

## 关键测试流程

1. **图构建** (`TestBuildOrderGraph`): 覆盖线性（A→B→C）、环（C→A 闭合）和孤立节点，验证节点与边的数量及邻接方向。
2. **层级计算** (`TestComputeNodeLevels`):
   - **DAG**: 线性链层级递增；扇出结构中 B、C 同层。
   - **含环图**: SCC 内节点共享同一层级；带尾巴的环中，尾巴节点比环高一层。
   - **不连通图**: 各部分独立从第 0 层开始计算。
3. **源节点查找** (`TestFindSourceNodes`):
   - **DAG**: 返回入度为 0 的节点（可用 `set` 断言顺序无关）。
   - **纯环**: 将 SCC 整体视为源，返回其中一个代表点。
   - **轮状拓扑**: Center 指向环形 Ring，Center 是唯一 source。
4. **深图回归** (`TestDeepGraphRegression`):
   - 深链（5000 节点）：`tarjan_scc` 全部为单点 SCC、源节点为 `n0`、层级线性递增到 4999。
   - 深环（5000 节点）：全部节点收敛为单一 SCC。
   - 深链经 `TaskGraph`（`graph_mode="thread"`）全链路建图与分析不崩溃，`layersDict[4999] == ["n4999"]`。

## 测试辅助函数
- `_make_graph(edges)`: 从边定义（含隐式出现的下游节点）构造测试图。
- `_make_chain(depth)`: 构造 `depth` 个节点的线性链。
- `_make_ring(size)`: 构造 `size` 个节点的闭合环。

## 测试重点
- **OrderGraph 构建**: 确保内部有序图结构与邻接关系正确。
- **层级一致性**: 复杂拓扑（如带尾巴的环）下层级计算的鲁棒性。
- **SCC 处理**: 确保循环引用不会导致死循环或错误的层级/源节点分布。
- **递归安全**: `tarjan_scc` 曾为递归实现，深链/深环会触发 `RecursionError`；改为迭代实现后超深图应能正常完成分析。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_order_graph.py -v

# 仅运行图构建测试
pytest tests/graph/test_order_graph.py::TestBuildOrderGraph -v

# 仅运行层级计算测试
pytest tests/graph/test_order_graph.py::TestComputeNodeLevels -v

# 仅运行源节点查找测试
pytest tests/graph/test_order_graph.py::TestFindSourceNodes -v

# 仅运行深图回归测试
pytest tests/graph/test_order_graph.py::TestDeepGraphRegression -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestBuildOrderGraph` | < 0.1s（纯内存计算） |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |
| `TestDeepGraphRegression` | ~1s（5000 节点规模，纯内存计算） |

## 重要细节
- 除 `TestDeepGraphRegression.test_deep_chain_through_taskgraph` 外均为纯内存计算，执行速度极快。
- 深图用例将 `DEEP` 保持在 5000，兼顾回归覆盖与测试耗时。

## 注意事项
- 测试代码位于 `tests/graph/test_order_graph.py`，对应实现位于 `src/celestialflow/graph/util_order_graph.py`。
