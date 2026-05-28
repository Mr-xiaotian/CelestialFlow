# Graph 模块

> 📅 最后更新日期: 2026/05/28

Graph 模块是 CelestialFlow 的核心调度系统，负责管理任务节点之间的依赖关系、执行流程和生命周期。它提供了灵活的任务图构建、分析和序列化功能。

## 模块概述

Graph 模块定义了任务执行的基本单元和它们之间的关系，形成一个有向图。每个节点代表一个 `TaskStage`，边代表数据流依赖关系。该模块确保任务按照正确的拓扑顺序执行，并处理并发、错误处理和资源管理。

## 文件说明

### 核心文件

1. **core_graph.py** (`TaskGraph`)
   - **作用**: 核心调度器，管理 `TaskStage` 节点的依赖关系、执行流程、资源分配和生命周期
   - **关键功能**:
     - 建立节点间的依赖关系（`set_stages` / `connect`）
     - 执行任务图（`eager` 一次性启动 / `staged` 分层执行）
     - 运行时监控快照和全局剩余时间估算
     - 动态任务注入（`put_stage_queue`）
     - 错误持久化和未消费任务处理

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

3. **util_analysis.py**
   - **作用**: 基于 `networkx` 的图分析工具
   - **关键函数**:
     - `build_networkx_graph()`: 从邻接表和运行时信息构建 `DiGraph`
     - `find_source_nodes()`: 找到入度为 0 的源节点
     - `compute_node_levels()`: 计算节点层级（支持 DAG 和含环图）

4. **util_serialize.py**
   - **作用**: 任务图结构序列化为 JSON 及文本化
   - **关键函数**:
     - `build_structure_graph()`: 从源节点递归构建结构 JSON
     - `_build_structure_subgraph()`: 递归构建子图（内部函数）
     - `format_structure_list_from_graph()`: 格式化为可打印树形文本

## 模块关联

### 内部关联
- `TaskGraph` 是基础类，所有其他结构继承自它
- `TaskChain`、`TaskLoop` 等是 `TaskGraph` 的特化实现（封装了 `set_stages` / `connect` 逻辑）
- 分析工具依赖 `networkx` 进行图论计算
- 序列化工具将运行时结构输出为 JSON/文本

### 外部关联
- **与 Stage 模块**: `TaskGraph` 管理 `TaskStage` 节点，每个节点通过 `start_stage` 启动
- **与 Runtime 模块**: 使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Persistence 模块**: 通过 `LogSpout`/`FailSpout` 实现持久化
- **与 Observability 模块**: 通过 `TaskReporter` 向 Web UI 推送状态

## 使用模式

1. **构建任务图**: 创建 `TaskStage` 节点 → `set_stages()` 注册 → `connect()` 建立依赖
2. **选择结构**: 对常见模式可直接使用 `TaskChain`/`TaskCross` 等预定义结构
3. **配置**: 通过 `set_reporter()` / `set_ctree()` 集成外部服务
4. **执行**: 调用 `start_graph()` 或子类的 `start_chain()`/`start_cross()` 等方法
5. **监控**: 使用 `collect_runtime_snapshot()` 和 `get_graph_summary()` 获取状态

## 使用示例

以下示例展示 graph 模块的各种图结构的构建和执行方式。

### 基础 TaskGraph 构建

```python
from celestialflow import TaskGraph, TaskStage

# 定义阶段函数
def stage_a_func(x: int) -> int:
    return x + 1

def stage_b_func(x: int) -> int:
    return x * 2

def stage_c_func(x: int) -> int:
    return x - 3

# 创建节点
s1 = TaskStage("S1", func=stage_a_func, execution_mode="serial")
s2 = TaskStage("S2", func=stage_b_func, execution_mode="serial")
s3 = TaskStage("S3", func=stage_c_func, execution_mode="serial")

# 构建 DAG: S1 -> S2 -> S3
graph = TaskGraph(schedule_mode="eager")
graph.set_stages([s1, s2, s3])
graph.connect([s1], [s2])
graph.connect([s2], [s3])

# 执行
graph.start_graph({s1.get_name(): [1, 2, 3]})

# 查看摘要
summary = graph.get_graph_summary()
print(f"图摘要: {summary}")

# 图分析
analysis = graph.get_graph_analysis()
print(f"是DAG: {analysis['isDAG']}")
print(f"层级: {analysis['layersDict']}")
```

### TaskChain 线性链

```python
from celestialflow import TaskChain, TaskStage

stages = [
    TaskStage("Clean", func=lambda x: x.strip().lower()),
    TaskStage("Parse", func=lambda x: int(x)),
    TaskStage("Compute", func=lambda x: x ** 2),
]

chain = TaskChain(stages, chain_mode="serial")
chain.start_chain({stages[0].get_name(): [" 10 ", " 20 ", " 30 "]})

print(f"链摘要: {chain.get_graph_summary()}")
```

### TaskCross 交叉层

```python
from celestialflow import TaskCross, TaskStage

# 定义两层
layer1 = [TaskStage("F1", func=lambda x: x * 2), TaskStage("F2", func=lambda x: x + 3)]
layer2 = [TaskStage("G1", func=lambda x: x ** 2), TaskStage("G2", func=lambda x: -x)]

cross = TaskCross(layers=[layer1, layer2], schedule_mode="eager")
cross.start_cross({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [10, 20]})
print(cross.get_graph_summary())
```

### TaskGrid 网格

```python
from celestialflow import TaskGrid, TaskStage

s00 = TaskStage("A", func=lambda x: x)
s01 = TaskStage("B", func=lambda x: x + 1)
s10 = TaskStage("C", func=lambda x: x * 2)
s11 = TaskStage("D", func=lambda x: x * x)

grid = TaskGrid(grid=[[s00, s01], [s10, s11]])
grid.start_grid({s00.get_name(): [1, 2]})
print(grid.get_graph_summary())
```

### TaskLoop 环形图

```python
from celestialflow import TaskLoop, TaskStage

stages = [
    TaskStage("L1", func=lambda x: x + 1),
    TaskStage("L2", func=lambda x: x * 2),
    TaskStage("L3", func=lambda x: x - 1),  # L3 -> L1 形成环
]

loop = TaskLoop(stages)
# 环结构建议 put_termination_signal=False 避免提前终止
loop.start_loop({stages[0].get_name(): [10]}, put_termination_signal=False)
```

### TaskWheel 轮状图

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Center", func=lambda x: f"processed: {x}")
ring = [TaskStage(f"R{i}", func=lambda x: f"ring-{i}: {x}") for i in range(3)]

wheel = TaskWheel(center=center, ring=ring)
wheel.start_wheel({center.get_name(): ["data"]})
```

## 最佳实践

- 线性流程使用 `TaskChain`，无需手动 `connect`
- 多路并行流水线使用 `TaskCross` 或手动组合
- 有环图（`TaskLoop`/`TaskWheel`）建议 `put_termination_signal=False`，通过外部注入停止
- 生产环境启用 `set_reporter(True)` 进行 Web 监控
- 复杂 DAG 使用 `staged` 模式便于逐层调试
