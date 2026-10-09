# src/celestialflow/graph/__init__.py

> 📅 最后更新日期: 2026/10/09

Graph 模块是 CelestialFlow 的核心调度系统，负责管理任务节点之间的依赖关系、执行流程和生命周期。它提供了灵活的任务图构建与分析功能。

## 模块概述

Graph 模块定义了任务执行的基本单元和它们之间的关系，形成一个有向图。每个节点是 `celestialflow.node` 中定义的 `BaseTaskNode` 派生对象（公共 API 包括 `TaskExecutor`、`TaskSplitter`、`TaskRouter`），边代表数据流依赖关系。该模块确保任务按照正确的拓扑顺序执行，并处理并发、错误处理和资源管理。

### 公开导出符号 (`__all__`)

```python
from celestialflow.graph import (
    TaskChain,  # 线性任务链
    TaskComplete,  # 完全图结构
    TaskCross,  # 多层交叉结构
    TaskGraph,  # 核心任务图
    TaskGrid,  # 二维网格结构
    TaskLoop,  # 环形结构
    TaskWheel,  # 轮状结构
)
```

`__all__ = ["TaskChain", "TaskComplete", "TaskCross", "TaskGraph", "TaskGrid", "TaskLoop", "TaskWheel"]`

## 文件说明

### 核心文件

1. **core_graph.py** (`TaskGraph`)
   - **作用**: 核心调度器，管理任务节点（`BaseTaskNode` 派生对象）的依赖关系、执行流程与生命周期
   - **关键功能**:
     - 建立节点间的依赖关系（`set_nodes` / `connect`）
     - 执行任务图（`start` / `start_async`，按 `graph_mode` 串行/线程/异步执行）
     - 批量设置节点执行模式（`set_node_execution_mode`）与共享事件客户端（`set_ctree`）
     - 图级观察者注册（`add_observer`）与查询（`get_observers`）
     - 图分析（`_build_analysis`：源节点识别、DAG 判定、层级计算）
     - 初始任务与持久化任务注入（`run` / `run_async` / `restore_db` / `inject_tasks` / `inject_terminations`）

2. **core_structure.py**（预定义图结构）
   - **作用**: 提供六种预定义的任务图结构，简化常见模式
   - **包含的结构**:
     - `TaskChain`: 线性任务链，节点按顺序连接
     - `TaskLoop`: 环形结构，节点首尾相连
     - `TaskCross`: 多层交叉结构，层内并行、层间全连接
     - `TaskComplete`: 完全图，每个节点连接所有其他节点
     - `TaskWheel`: 轮辐结构，中心节点连接环上所有节点
     - `TaskGrid`: 二维网格，节点连接右侧和下方邻居

### 工具文件

3. **util_order_graph.py**
   - **作用**: 轻量级有序有向图与基础图算法工具
   - **关键内容**:
     - `OrderGraph`: 最小有序有向图，维护稳定节点顺序、入边和出边邻接表
     - `is_dag()` / `topo_sort()`: DAG 判定与拓扑排序
     - `tarjan_scc()` / `get_condensation()`: 强连通分量分析与凝聚图构建
     - `source_sccs()` / `source_nodes()`: 定位源 SCC 并提取代表性源节点
     - `compute_node_levels()`: 基于 SCC 凝聚图计算节点层级

> 说明：图结构的树形文本渲染（`render_structure_list`）已从本模块迁往 `persist/util_render.py`，Graph 模块不再持有渲染逻辑。

## 模块关联

### 内部关联
- `TaskGraph` 是基础类，所有其他结构继承自它
- `TaskChain`、`TaskLoop` 等是 `TaskGraph` 的特化实现（封装了 `set_nodes` / `connect` 逻辑）
- `util_order_graph.py` 提供框架内部统一复用的轻量图结构和基础图算法
- `TaskGraph` 当前基于 `OrderGraph` 完成源节点识别、DAG 判定与层级分析

### 外部关联
- **与 Node 模块**: 任务图节点（`TaskExecutor` / `TaskSplitter` / `TaskRouter`）由 `celestialflow.node` 提供，`TaskGraph` 仅负责装配、连接与调度
- **与 Runtime 模块**: 使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Observer 模块**: 通过 `add_observer()` 注册图级观察者，接收图中所有节点的事件；运行时资源通过 `run_graph_resources` 统一管理
- **与 Persistence 模块**: 通过持久化入口（lifecycle / log）实现任务持久化与恢复（`restore_db`）

## 使用模式

1. **构建任务图**: 创建 `TaskExecutor` 节点（按需使用 `TaskSplitter` / `TaskRouter`）→ `set_nodes()` 注册 → `connect()` 建立依赖
2. **选择结构**: 对常见模式可直接使用 `TaskChain`/`TaskCross` 等预定义结构
3. **配置**: 通过 `set_ctree()` 注入事件客户端、`add_observer()` 注册图级观察者
4. **执行**: 调用 `run()` 或 `run_async()`

## 使用示例

以下示例展示 graph 模块的各种图结构的构建和执行方式。

### 基础 TaskGraph 构建

```python
from celestialflow import TaskGraph, TaskExecutor

# 定义阶段函数
def stage_a_func(x: int) -> int:
    return x + 1


def stage_b_func(x: int) -> int:
    return x * 2


def stage_c_func(x: int) -> int:
    return x - 3


# 创建节点
s1 = TaskExecutor("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskExecutor("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskExecutor("S3", func=stage_c_func, execution_mode="serial")

# 构建 DAG: S1 -> S2 -> S3
graph = TaskGraph(name="MyGraph", graph_mode="thread")
graph.set_nodes([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 执行
graph.run({s1.get_name(): [1, 2, 3]})

# 图分析
print(f"源节点: {graph.get_source_nodes()}")
print(f"节点列表: {graph.get_nodes()}")
print(f"边邻接表: {graph.get_edges()}")
```

### TaskChain 线性链

```python
from celestialflow import TaskChain, TaskExecutor

nodes = [
    TaskExecutor("Clean", func=lambda x: x.strip().lower()),
    TaskExecutor("Parse", func=lambda x: int(x)),
    TaskExecutor("Compute", func=lambda x: x**2),
]

chain = TaskChain(name="DataPipeline", nodes=nodes, graph_mode="thread")
chain.run({nodes[0].get_name(): [" 10 ", " 20 ", " 30 "]})

# 查看节点与来源
print(chain.get_nodes())
```

### TaskCross 交叉层

```python
from celestialflow import TaskCross, TaskExecutor

# 定义两层
layer1 = [
    TaskExecutor("F1", func=lambda x: x * 2),
    TaskExecutor("F2", func=lambda x: x + 3),
]
layer2 = [
    TaskExecutor("G1", func=lambda x: x**2),
    TaskExecutor("G2", func=lambda x: -x),
]

cross = TaskCross(name="CrossPipeline", layers=[layer1, layer2], graph_mode="thread")
cross.run({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
```

### TaskGrid 网格

```python
from celestialflow import TaskGrid, TaskExecutor

s00 = TaskExecutor("A", func=lambda x: x)
s01 = TaskExecutor("B", func=lambda x: x + 1)
s10 = TaskExecutor("C", func=lambda x: x * 2)
s11 = TaskExecutor("D", func=lambda x: x * x)

grid = TaskGrid(name="GridPipeline", grid=[[s00, s01], [s10, s11]])
grid.run({s00.get_name(): [1, 2]})
```

### TaskLoop 环形图

```python
from celestialflow import TaskLoop, TaskExecutor

nodes = [
    TaskExecutor("L1", func=lambda x: x + 1),
    TaskExecutor("L2", func=lambda x: x * 2),
    TaskExecutor("L3", func=lambda x: x - 1),  # L3 -> L1 形成环
]

loop = TaskLoop(name="FeedbackLoop", nodes=nodes)
# 环结构建议 if_put_signal=False 避免提前终止
loop.run({nodes[0].get_name(): [10]}, if_put_signal=False)
```

### TaskWheel 轮状图

```python
from celestialflow import TaskWheel, TaskExecutor

center = TaskExecutor("Center", func=lambda x: f"processed: {x}")
ring = [TaskExecutor(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(name="HubAndSpoke", center=center, ring=ring)
wheel.run({center.get_name(): ["data"]})
```

## 最佳实践

- 线性流程使用 `TaskChain`，无需手动 `connect`
- 多路并行流水线使用 `TaskCross` 或手动组合
- 有环图（`TaskLoop`/`TaskWheel`）建议 `if_put_signal=False`，通过外部注入停止
- 需要监控/接收图中事件时使用 `add_observer()` 注册图级观察者
- 异步执行使用 `TaskGraph` 的 `graph_mode="async"`，并通过 `start_async()` / `run_async()` 启动