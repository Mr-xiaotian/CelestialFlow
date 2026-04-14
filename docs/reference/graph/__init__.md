# Graph 模块

Graph 模块是 CelestialFlow 的核心调度系统，负责管理任务节点之间的依赖关系、执行流程和生命周期。它提供了灵活的任务图构建、分析和序列化功能。

## 模块概述

Graph 模块定义了任务执行的基本单元和它们之间的关系，形成一个有向无环图（DAG）。每个节点代表一个 `TaskStage`，边代表依赖关系。该模块确保任务按照正确的顺序执行，并处理并发、错误处理和资源管理。

## 文件说明

### 核心文件

1. **core_graph.py** (`TaskGraph`)
   - **作用**: 核心调度器，管理 `TaskStage` 节点的依赖关系、执行流程、资源分配和生命周期
   - **关键功能**:
     - 建立节点间的依赖关系
     - 执行任务图（同步/异步）
     - 错误处理和重试机制
     - 资源管理和并发控制

2. **core_structure.py** (`TaskChain`, `TaskLoop`, `TaskCross`, `TaskComplete`, `TaskWheel`, `TaskGrid`)
   - **作用**: 提供预定义的任务图结构，简化常见模式的构建
   - **包含的结构**:
     - `TaskChain`: 线性任务链，节点按顺序执行
     - `TaskLoop`: 循环结构，支持条件循环
     - `TaskCross`: 交叉连接结构，节点间相互连接
     - `TaskComplete`: 完全连接结构，所有节点相互连接
     - `TaskWheel`: 轮辐结构，中心节点连接所有其他节点
     - `TaskGrid`: 网格结构，节点按行列排列

### 工具文件

3. **util_analysis.py**
   - **作用**: 任务图分析工具，提供图论分析和诊断功能
   - **关键函数**:
     - `format_networkx_graph()`: 将结构图转换为 networkx 有向图
     - `compute_node_levels()`: 计算图中节点的层级（拓扑排序）
   - **关键功能**:
     - 图结构转换和可视化支持
     - 节点层级计算和拓扑分析
     - 依赖关系分析和验证

4. **util_serialize.py**
   - **作用**: 任务图序列化和结构构建工具
   - **关键函数**:
     - `build_structure_graph()`: 从根节点构建任务链的 JSON 图结构
     - `_build_structure_subgraph()`: 构建单个子图结构（内部函数）
     - `format_structure_list_from_graph()`: 从图结构格式化字符串列表
   - **关键功能**:
     - 任务图结构序列化为 JSON 格式
     - 递归构建图结构表示
     - 结构格式化和文本输出

## 模块关联

### 内部关联
- `TaskGraph` 是基础类，所有其他结构都继承或使用它
- `TaskChain`、`TaskLoop` 等是 `TaskGraph` 的特化实现
- 分析工具依赖图结构进行诊断
- 序列化工具可以将任何 `TaskGraph` 实例持久化

### 外部关联
- **与 Stage 模块**: 管理 `TaskStage` 节点，每个节点都是可执行单元
- **与 Runtime 模块**: 使用 `TaskDispatch` 执行任务，依赖 `TaskQueue` 进行通信
- **与 Persistence 模块**: 通过序列化工具与持久化存储交互
- **与 Observability 模块**: 提供执行状态和性能指标

## 使用模式

1. **构建任务图**: 创建 `TaskStage` 节点，配置各节点的 `set_graph_context()`，建立依赖关系
2. **选择结构**: 根据需求使用预定义结构（如 `TaskChain` 用于线性流程）
3. **执行**: 调用 `start_graph()` 或通过子类的 `start_chain()` 等方法执行任务图
4. **监控**: 使用分析工具检查图结构，监控执行状态
5. **持久化**: 需要时使用序列化工具保存/加载任务图

## 最佳实践

- 对于简单线性流程，优先使用 `TaskChain`
- 复杂分支逻辑使用 `TaskSplitter` 和 `TaskRouter`
- 循环任务使用 `TaskLoop`
- 定期使用分析工具检查图结构的健康状态
- 重要工作流建议序列化保存，便于调试和恢复