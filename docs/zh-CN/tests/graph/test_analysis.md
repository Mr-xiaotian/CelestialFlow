# 图分析工具测试 (test_analysis.py)

> 最后更新日期: 2026/06/18

## 作用
验证 `celestialflow.graph.util_graph` 中的基础图分析函数，确保 `OrderGraph` 构建、层级计算和源节点查找逻辑的准确性。

## 核心测试对象
- `OrderGraph.from_edges`: 将邻接表转换为 `OrderGraph`。
- `compute_node_levels`: 计算图中各节点的逻辑层级。
- `source_nodes`: 查找图的入口节点（源节点）。

## 关键测试流程
1. **图构建测试**: 覆盖线性、含环和孤立节点场景，验证节点和边的数量及方向。
2. **层级计算测试**:
   - **DAG**: 验证线性链、扇出结构的层级递增。
   - **含环图**: 验证强连通分量（SCC）内的节点共享同一层级。
   - **不连通图**: 验证各连通分量独立从第 0 层开始计算。
3. **源节点查找测试**:
   - **DAG**: 查找入度为 0 的节点。
   - **纯环**: 将 SCC 整体视为源，返回其中一个代表点。
   - **轮式拓扑**: 验证中心节点被识别为唯一源。

## 测试重点
- **OrderGraph 构建**: 确保内部有序图结构与邻接关系正确。
- **层级一致性**: 复杂拓扑（如带尾巴的环）下层级计算的鲁棒性。
- **SCC 处理**: 确保循环引用不会导致死循环或错误的层级分布。

## 运行方式

```bash
# 全部执行
pytest tests/graph/test_analysis.py -v

# 仅运行图构建测试
pytest tests/graph/test_analysis.py::TestBuildOrderGraph -v

# 仅运行层级计算测试
pytest tests/graph/test_analysis.py -k "levels" -v

# 仅运行源节点查找测试
pytest tests/graph/test_analysis.py -k "source" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestBuildOrderGraph` | < 0.1s（纯内存计算） |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## 重要细节
- 测试用例均为纯内存计算，执行速度极快。

## 注意事项
- 测试代码位于 `tests/graph/test_analysis.py`，对应实现位于 `src/celestialflow/graph/util_graph.py`。
