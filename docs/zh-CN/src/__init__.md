# CelestialFlow 包入口

> 📅 最后更新日期: 2026/06/17

## 简介

本项目根入口，从各子模块集中导出全部公开 API，用户只需 `from celestialflow import ...` 即可访问所有核心功能。

## 模块分组

按来源模块分类，每个组说明其主要用途。

---

### graph — 任务图核心

提供多种拓扑结构定义，支持 DAG 构建、依赖连接与执行调度。

| 导出符号 | 说明 |
|----------|------|
| `TaskGraph` | 通用任务图容器，支持任意 DAG 拓扑 |
| `TaskChain` | 线性链式结构（前一节点 → 后一节点） |
| `TaskCross` | 交叉连接结构（多源 × 多目标） |
| `TaskGrid` | 网格状连接结构 |
| `TaskLoop` | 循环结构，节点可在满足条件时回环 |
| `TaskWheel` | 轮状结构，一个中心节点连接多个外围节点 |
| `TaskComplete` | 全连接结构，所有节点两两相连 |

---

### stage — 任务执行层

提供任务执行器、路由分发与任务拆分等执行层能力。

| 导出符号 | 说明 |
|----------|------|
| `TaskExecutor` | 通用任务执行器，支持 serial / thread / async 三种执行模式 |
| `TaskStage` | 图中的一个任务节点，包裹执行函数与配置 |
| `TaskSplitter` | 任务拆分器，将一个输入拆分为多个子任务 |
| `TaskRouter` | 路由分发器，根据规则将任务分发到不同下游 |
| `TerminationSignal` | 终止信号，用于控制图执行流程的结束 |

---

### observability — 可观测性

提供观察者模式支持，用于监控任务执行过程。

| 导出符号 | 说明 |
|----------|------|
| `BaseObserver` | 观察者基类，定义 on_start / on_success / on_failure 等接口 |
| `CallbackObserver` | 回调式观察者，通过传入回调函数处理事件 |
| `TaskProgress` | 任务进度追踪器，实时统计完成/失败/总数 |

---

### utils — 工具集

提供基准测试与格式化工具。

| 导出符号 | 说明 |
|----------|------|
| `benchmark_executor` | 对同步/异步 `TaskExecutor` 进行多模式基准测试 |
| `benchmark_graph` | 对整个任务图进行基准测试 |
| `format_table` | 格式化表格输出，用于控制台展示对比数据 |

---

### web — Web 服务

提供内置 Web 服务器，用于图状态监控与可视化。

| 导出符号 | 说明 |
|----------|------|
| `TaskWebServer` | 基于 FastAPI 的 Web 服务器，提供图运行时快照的 HTTP API 和可视化面板 |

---

### persistence — 持久化

提供 JSONL 日志的加载与查询功能。

| 导出符号 | 说明 |
|----------|------|
| `load_jsonl_logs` | 加载 JSONL 格式的日志文件 |
| `load_task_by_stage` | 按阶段名称筛选加载任务日志 |
| `load_task_by_error` | 按错误类型筛选加载任务日志 |

---

### runtime — 运行时工具

提供运行时辅助类型与工具函数。

| 导出符号 | 说明 |
|----------|------|
| `make_hashable` | 将不可哈希对象（如 dict、list）转为可哈希形式 |
| `TerminationSignal` | 终止信号（与 stage 组共用同一符号） |

---

## `__all__` 列表

完整公开 API 列表（当前共 23 个符号）：

```python
__all__ = [
    "TaskGraph",
    "TaskChain",
    "TaskLoop",
    "TaskCross",
    "TaskComplete",
    "TaskWheel",
    "TaskGrid",
    "BaseObserver",
    "CallbackObserver",
    "TaskProgress",
    "TaskExecutor",
    "TaskStage",
    "TaskSplitter",
    "TaskRouter",
    "TerminationSignal",
    "TaskWebServer",
    "load_jsonl_logs",
    "load_task_by_stage",
    "load_task_by_error",
    "make_hashable",
    "format_table",
    "benchmark_graph",
    "benchmark_executor",
]
```

## 使用示例

以下示例演示如何从包入口导入并使用 CelestialFlow 的核心功能构建和执行任务图。

```python
from celestialflow import TaskGraph, TaskStage, TaskExecutor

# 1. 定义任务处理函数
def double(x: int) -> int:
    return x * 2

def add_one(x: int) -> int:
    return x + 1

# 2. 创建 TaskStage 节点
stage_a = TaskStage("StageA", func=double, execution_mode="serial", stage_mode="serial")
stage_b = TaskStage("StageB", func=add_one, execution_mode="serial", stage_mode="serial")

# 3. 构建 DAG 图
graph = TaskGraph()
graph.set_stages([stage_a, stage_b])
graph.connect([stage_a], [stage_b])

# 4. 执行图
init_tasks = {stage_a.get_name(): [1, 2, 3, 4, 5]}
graph.start_graph(init_tasks)

# 5. 查看执行结果摘要
summary = graph.get_graph_summary()
print("Graph summary:", summary)
```

### 使用 TaskExecutor 独立执行

`TaskExecutor` 可脱离图结构独立运行，适合单步任务执行：

```python
from celestialflow import TaskExecutor

# 创建执行器并传入数据迭代器
executor = TaskExecutor("Adder", func=lambda x: x + 10, execution_mode="serial")
executor.start([1, 2, 3])

# 获取执行结果
success_pairs = executor.get_success_pairs()
for task, result in success_pairs:
    print(f"Task: {task} -> Result: {result}")

# 查看统计计数
counts = executor.get_counts()
print("Counts:", counts)
```

### 使用预定义图结构

```python
from celestialflow import TaskChain, TaskStage

stages = [
    TaskStage("S1", func=lambda x: x * 2),
    TaskStage("S2", func=lambda x: x + 1),
    TaskStage("S3", func=lambda x: x ** 2),
]

chain = TaskChain(stages, chain_mode="serial")
chain.start_chain({stages[0].get_name(): [1, 2, 3]})
summary = chain.get_graph_summary()
print("Chain summary:", summary)
```

## 模块依赖关系

```mermaid
graph TD
    subgraph "CelestialFlow 包入口"
        Init["__init__.py"]
    end

    subgraph graph
        G["TaskGraph<br/>TaskChain<br/>TaskLoop<br/>TaskCross<br/>TaskComplete<br/>TaskWheel<br/>TaskGrid"]
    end

    subgraph stage
        S["TaskExecutor<br/>TaskStage<br/>TaskSplitter<br/>TaskRedisTransport<br/>TaskRedisSource<br/>TaskRedisAck<br/>TaskRouter<br/>TerminationSignal"]
    end

    subgraph observability
        O["BaseObserver<br/>CallbackObserver<br/>TaskProgress"]
    end

    subgraph utils
        U["benchmark_executor<br/>benchmark_graph<br/>format_table"]
    end

    subgraph web
        W["TaskWebServer"]
    end

    subgraph persistence
        P["load_jsonl_logs<br/>load_task_by_stage<br/>load_task_by_error"]
    end

    subgraph runtime
        R["make_hashable<br/>TerminationSignal"]
    end

    Init --> G
    Init --> S
    Init --> O
    Init --> U
    Init --> W
    Init --> P
    Init --> R
```
