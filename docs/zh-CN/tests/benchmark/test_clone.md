# tests/benchmark/test_clone.py

> 📅 最后更新日期: 2026/09/09

## 作用

验证 `celestialflow.benchmark.util_clone` 中的 `clone_executor` 与 `clone_graph` 克隆函数，确保深度复制后新对象与原对象属性一致且相互独立。其中 "graph node" 系列用例覆盖 `clone_executor` 在图节点上下文中的复用语义。

## 核心测试对象

- `clone_executor`: 复制 `TaskExecutor`，保留 `name`、`func`、`execution_mode`；同样适用于作为图节点使用的 `TaskExecutor` 实例。
- `clone_graph`: 复制 `TaskGraph`，保留完整的 DAG 结构（节点、边）与 `graph_mode`，且节点间相互独立。

## 关键测试场景

### `clone_executor`
- 克隆后 `name` / `func` / `execution_mode` 与原对象相同
- 克隆返回的是不同对象（`is not` 检查）
- 修改克隆的 `execution_mode` 不影响原对象

### `clone_executor` 作为图节点（`graph node`）
- 克隆后 `name` / `func` / `execution_mode` 与原节点相同
- 克隆返回的是不同对象
- 修改克隆的 `execution_mode` 不影响原节点

### `clone_graph`
- 简单 DAG（A→B→C）：克隆后源节点、`OrderGraph` 节点集合、出边邻接表均一致
- 克隆图中修改某节点的 `execution_mode` 不影响原图对应节点
- 默认本地事件客户端在克隆后应保持实例独立
- 带 `TaskReporter` 的图在克隆后应绑定新的 reporter 实例（`cloned.reporter.task_graph is cloned`）

## 测试覆盖矩阵

| 测试函数 | 覆盖目标 |
|----------|----------|
| `test_clone_executor_same_attributes` | 克隆后关键属性一致 |
| `test_clone_executor_different_object` | 克隆返回新对象 |
| `test_clone_executor_independent` | 修改克隆不影响原执行器 |
| `test_clone_graph_node_same_attributes` | 作为图节点时，`clone_executor` 保留核心属性 |
| `test_clone_graph_node_different_object` | 作为图节点时，克隆返回独立对象 |
| `test_clone_graph_node_independent` | 作为图节点时，修改克隆不影响原节点 |
| `test_clone_graph_structure` | DAG 结构、源节点、`OrderGraph` 节点与边一致 |
| `test_clone_graph_independent` | 克隆图节点修改不影响原图 |
| `test_clone_graph_creates_independent_local_event_client` | 本地事件客户端实例独立 |
| `test_clone_graph_rebinds_task_reporter_to_cloned_graph` | 带 TaskReporter 的图在克隆后绑定新的 reporter 实例 |

## 运行方式

```bash
# 全部执行
pytest tests/benchmark/test_clone.py -v

# 仅运行 executor 克隆测试
pytest tests/benchmark/test_clone.py -k "executor" -v

# 仅运行 graph 节点 / graph 克隆测试
pytest tests/benchmark/test_clone.py -k "graph" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestUtilClone` | ~0.1s |

## 重要细节

- 克隆图后通过 `get_order_graph()` 返回的 `OrderGraph` 验证节点集合与出边邻接表一致；访问 `get_source_nodes()` 会同时触发克隆图的 `_build_analysis`。
- `clone_graph` 测试构造了有向无环图 `A → B → C`，验证图结构完整性。
- `LocalEventClient` 独立验证确保克隆图拥有独立的事件总线，避免运行时状态互相干扰。
- 带 `TaskReporter` 的图在克隆后应绑定新的 reporter 实例，`cloned.reporter.task_graph` 指向克隆图。
- 文件末尾的 `# 运行方式` 注释与上方 `pytest` 命令一致，便于直接复制运行。

## 注意事项

- 克隆工具用于 `benchmark_graph` 内部复制图结构以实现不同模式组合的独立执行。
- 相关实现位于 `src/celestialflow/benchmark/util_clone.py`。
