# test_analysis.py 测试说明

> 📅 最后更新日期: 2026/05/15

## 测试目标

验证 `celestialflow.graph.util_analysis` 模块中的图分析工具函数，包括：
- NetworkX 有向图的构建（`build_networkx_graph`）
- 节点层级计算（`compute_node_levels`），含 DAG 和含环图
- 源节点查找（`find_source_nodes`），含纯环和轮式拓扑

## 测试范围

| 测试类 | 用例数 | 覆盖点 |
|--------|--------|--------|
| `TestBuildNetworkxGraph` | 3 | 线性图、含环图、孤立节点 |
| `TestComputeNodeLevels` | 5 | 线性 DAG、扇出 DAG、单环、环+尾巴、断开图 |
| `TestFindSourceNodes` | 4 | 线性 DAG、多源、纯环、轮式拓扑 |

### 关键用例详解

#### `test_linear`
- **目标**：验证 A → B → C 线性图的节点数、边数和后继关系。
- **断言**：3 个节点、2 条边，A 的后继为 B。

#### `test_cycle`
- **目标**：验证含环图（A → B → C → A）的正确构建。
- **断言**：3 个节点、3 条边，C 的后继包含 A。

#### `test_isolated_node`
- **目标**：验证无边的孤立节点图。
- **断言**：2 个节点、0 条边。

#### `test_fan_out_dag`
- **目标**：A → {B, C} → D 扇出 DAG 的层级计算。
- **断言**：A 在第 0 层，B 和 C 在第 1 层，D 在第 2 层。

#### `test_single_cycle`
- **目标**：纯环（A → B → C → A）中所有节点属于同一 SCC，共享层级。
- **断言**：A、B、C 层级相同。

#### `test_cycle_with_tail`
- **目标**：环（A → B → C → A）加尾巴（A → D），D 比环高一层。
- **断言**：环内节点同层，D 在环层级 + 1。

#### `test_disconnected`
- **目标**：两条独立链（A → B，X → Y）各自从第 0 层开始。

#### `test_pure_cycle`（FindSourceNodes）
- **目标**：纯环无 `in_degree=0` 节点，但整个 SCC 作为一个 source 返回。
- **断言**：返回 1 个 source，属于环内节点。

#### `test_wheel_topology`
- **目标**：轮式拓扑（Center → {R1, R2, R3}，R1 → R2 → R3 → R1），Center 是唯一 source。

## 依赖

| 依赖 | 说明 |
|------|------|
| `pytest` | 测试框架 |
| `networkx` | 图数据结构 |
| `celestialflow.graph.util_analysis` | `build_networkx_graph`、`compute_node_levels`、`find_source_nodes` |

## 运行方式

```bash
pytest tests/test_analysis.py -v
```

所有用例均为纯内存图计算，执行时间 `< 100ms`。

## 相关文件

- `src/celestialflow/graph/util_analysis.py`：被测实现
- `tests/test_graph.py`：在 `TaskGraph` 集成场景中间接使用分析函数
