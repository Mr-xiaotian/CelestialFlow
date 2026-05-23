# Stage 模块

> 📅 最后更新日期: 2026/04/24

Stage 模块定义了 CelestialFlow 中的任务执行单元。它提供了从基础任务执行器到复杂任务节点的完整体系，是构建任务图的基本构建块。

## 模块概述

Stage 模块包含三个层次的任务执行单元：
1. **TaskExecutor**: 基础任务执行器，处理单一任务的执行逻辑
2. **TaskStage**: 增强型任务节点，增加了图连接能力
3. **预定义节点**: 常见任务模式的实现，如分流器、路由器等

这些组件共同构成了任务执行的核心，每个组件都可以独立使用或组合成复杂的任务流。

## 文件说明

### 核心文件

1. **core_executor.py** (`TaskExecutor`)
   - **作用**: 基础任务执行器，处理单一任务的执行、并发控制、错误处理和重试机制
   - **关键功能**:
     - 同步/异步任务执行
     - 错误处理和重试策略
     - 超时控制
     - 进度报告和日志记录
     - 资源管理和清理

2. **core_stage.py** (`TaskStage`)
   - **作用**: 增强型任务节点，继承自 `TaskExecutor`，增加了图结构连接能力
   - **关键功能**:
     - 支持输入/输出队列连接
     - 自动依赖管理
     - 图结构感知的执行
     - 支持并行和串行连接
     - 状态管理和生命周期控制

3. **core_stages.py** (预定义节点: `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`)
   - **作用**: 常见任务模式和 Redis 集成节点的预实现，简化复杂工作流的构建
   - **包含的节点**:
     - `TaskSplitter`: 将输入分发给多个子任务
     - `TaskRouter`: 根据条件路由任务到不同的下游节点
     - `TaskRedisTransport`: 将任务发送到 Redis 队列，用于跨语言或分布式执行
     - `TaskRedisSource`: 从 Redis 队列消费任务，作为任务图的输入源
     - `TaskRedisAck`: 接收 Redis Worker 的执行结果，并确认任务完成

## 模块关联

### 内部关联
- `TaskStage` 继承自 `TaskExecutor`，扩展了图连接功能
- 预定义节点都是 `TaskStage` 的特化实现
- 所有节点都可以在 `TaskGraph` 中组合使用

### 外部关联
- **与 Graph 模块**: `TaskStage` 是 `TaskGraph` 的基本构建单元
- **与 Runtime 模块**: 使用 `TaskQueue` 进行节点间通信，依赖 `TaskDispatch` 执行
- **与 Utils 模块**: 使用工具函数进行数据处理和转换
- **与 Persistence 模块**: 支持任务状态的持久化保存

## 使用模式

### 基础使用
1. **创建执行器**: 继承 `TaskExecutor` 实现自定义业务逻辑
2. **包装为节点**: 使用 `TaskStage` 包装执行器，使其支持图连接
3. **构建图结构**: 将节点添加到 `TaskGraph`，建立依赖关系

### 高级使用
1. **使用预定义节点**: 直接使用 `TaskSplitter`、`TaskRouter` 等简化开发
2. **组合节点**: 将多个节点组合成复杂的数据处理流水线
3. **自定义节点**: 继承 `TaskStage` 创建领域特定的节点类型

## 设计原则

### 单一职责
- 每个 `TaskExecutor` 只处理单一类型的任务
- `TaskStage` 专注于图连接和状态管理
- 预定义节点实现特定的数据处理模式

### 可组合性
- 所有节点使用统一的接口，可以自由组合
- 支持链式调用和并行处理
- 输入/输出类型兼容性检查

### 可扩展性
- 通过继承轻松创建自定义节点
- 支持插件式架构
- 配置驱动，无需修改代码即可调整行为

## 使用示例

以下示例展示 stage 模块各核心类的典型用法。

### TaskExecutor 独立使用

```python
from celestialflow import TaskExecutor

# 定义处理函数
def process_item(x: int) -> dict:
    return {"input": x, "output": x * 10}

# 创建并执行
executor = TaskExecutor(
    name="Calculator",
    func=process_item,
    execution_mode="serial",
)
executor.start([1, 2, 3])

# 获取结果
success = executor.get_success_pairs()
for task, result in success:
    print(f"{task} -> {result}")

# 统计
print(f"成功: {executor.get_counts()['tasks_succeeded']}")
```

### TaskStage 作为图节点

```python
from celestialflow import TaskGraph, TaskStage

# 创建阶段节点
stage_a = TaskStage("StageA", func=lambda x: x + 1, stage_mode="thread")
stage_b = TaskStage("StageB", func=lambda x: x * 2, stage_mode="serial")

# 构建图
graph = TaskGraph()
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 执行
graph.start_graph({stage_a.get_name(): [5, 10, 15]})

# 阶段快照
for name, runtime in graph.stage_runtime_dict.items():
    summary = runtime.stage.get_summary()
    print(f"{name}: {summary}")

# 图摘要
print(graph.get_graph_summary())
```

### TaskSplitter 使用示例

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter

# 自定义分裂器：将字符串按逗号分裂
class CommaSplitter(TaskSplitter):
    def _split(self, *task):
        return tuple(task[0].split(","))

# 构建图
raw = TaskStage("Source", func=lambda x: x, stage_mode="serial")
splitter = CommaSplitter("Splitter")
processor = TaskStage("Process", func=lambda x: x.strip().upper(), stage_mode="thread")

graph = TaskGraph()
graph.set_stages([raw, splitter, processor])
graph.connect([raw], [splitter])
graph.connect([splitter], [processor])

graph.start_graph({raw.get_name(): ["a,b,c", "x,y,z"]})
print(graph.get_graph_summary())
```

### TaskRouter 使用示例

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter

# 定义一个生成路由信息的处理函数
def classify(x: int) -> tuple:
    if x > 0:
        return ("positive", x)
    else:
        return ("negative", x)

source = TaskStage("Source", func=classify, stage_mode="serial")
router = TaskRouter("Router")
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", stage_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", stage_mode="serial")

graph = TaskGraph()
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])  # 路由到两个下游

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
print(graph.get_graph_summary())
```

## 最佳实践

1. **简单任务**: 直接使用 `TaskExecutor` 或继承实现
2. **图节点**: 总是使用 `TaskStage` 或子类作为图节点
3. **数据处理**: 优先使用预定义节点，减少重复代码
4. **错误处理**: 在 `TaskExecutor` 级别实现健壮的错误处理
5. **资源管理**: 正确实现 `cleanup()` 方法释放资源