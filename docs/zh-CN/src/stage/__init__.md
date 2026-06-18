# Stage 模块

> 📅 最后更新日期: 2026/06/17

Stage 模块定义了 CelestialFlow 中的任务执行单元。它提供了从基础任务执行器到复杂任务节点的完整体系，是构建任务图的基本构建块。

## 导出符号

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `TaskExecutor` | `core_executor` | 基础任务执行器，支持 serial/thread/async 三种执行模式 |
| `TaskStage` | `core_stage` | 增强型任务节点，继承 TaskExecutor，增加图连接能力与 stage_mode 控制 |
| `TaskSplitter` | `core_stages` | 预定义节点：将单个任务拆分为多个子任务 |
| `TaskRouter` | `core_stages` | 预定义节点：根据条件路由任务到不同下游 |

> `AnyTaskStage` 类型别名定义在 `util_types.py`，未纳入 `__all__`。

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
     - Observer 模式生命周期广播
     - 结果收集与错误记录

2. **core_stage.py** (`TaskStage`)
   - **作用**: 增强型任务节点，继承自 `TaskExecutor`，增加了图结构连接能力
   - **关键功能**:
     - 支持 `stage_mode`（serial/thread）控制节点在 Graph 中的调度方式
     - Inlet 绑定（`set_inlet`）将 fail/log 队列接入持久化层
     - 前置节点计数器绑定（`prev_bindings`）
     - 状态管理和生命周期控制（`NOT_STARTED → RUNNING → STOPPED`）

3. **core_stages.py** (预定义节点: `TaskSplitter`, `TaskRouter`)
   - **作用**: 常见结构型任务模式的预实现
   - **包含的节点**:
     - `TaskSplitter`: 将输入分发给多个子任务
     - `TaskRouter`: 根据条件路由任务到不同的下游节点

4. **util_types.py** (`AnyTaskStage`)
   - **作用**: 提供 `TaskStage[Any, Any]` 的类型别名，用于任意泛型参数的 Stage 通配标注

## 模块关联

### 内部关联
- `TaskStage` 继承自 `TaskExecutor`，扩展了图连接功能
- 预定义节点都是 `TaskStage` 的特化实现
- 所有节点都可以在 `TaskGraph` 中组合使用

### 外部关联
- **与 Graph 模块**: `TaskStage` 是 `TaskGraph` 的基本构建单元
- **与 Runtime 模块**: 使用 `TaskInQueue` / `TaskOutQueue` 进行节点间通信，依赖 `TaskDispatch` 执行
- **与 Persistence 模块**: 通过 `FallbackInlet` / `LogInlet` 持久化任务状态
- **与 Observability 模块**: 通过 `add_observer()` 注册 `BaseObserver` 子类

## 使用示例

以下示例展示 stage 模块各核心类的典型用法。

### TaskExecutor 独立使用

```python
from celestialflow import TaskExecutor

# 定义处理函数
def process_item(x: int) -> int:
    return x * 10

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
```

### TaskRouter 使用示例

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter

# 定义路由函数：根据任务内容返回目标节点名称
def classify(x: int) -> str:
    if x > 0:
        return "positive"
    else:
        return "negative"

# 上游只产出原始任务
source = TaskStage("Source", func=lambda x: x, stage_mode="serial")

# Router 内部决定把任务送给哪个下游
router = TaskRouter("Router", classify)
pos = TaskStage("Positive", func=lambda x: f"POS: {x}", stage_mode="serial")
neg = TaskStage("Negative", func=lambda x: f"NEG: {x}", stage_mode="serial")

graph = TaskGraph()
graph.set_stages([source, router, pos, neg])
graph.connect([source], [router])
graph.connect([router], [pos, neg])

graph.start_graph({source.get_name(): [5, -3, 10, -8]})
```

## 设计原则

- **一次性对象**: `TaskExecutor` 和 `TaskStage` 均设计为一次性使用，完成一次运行后不应复用
- **单一职责**: 每个 `TaskExecutor` 只处理单一类型的任务
- **可组合性**: 所有节点使用统一接口，可以自由组合到 `TaskGraph` 中
