# Observability 模块

> 📅 最后更新日期: 2026/08/26

Observability 模块提供了 CelestialFlow 的可观测性功能，包括运行状态监控、Observer 模式和远程状态上报。它使任务执行过程变得透明、可监控。

## 导出符号

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `BaseObserver` | `core_observer` | 执行器生命周期观察者基类，定义 `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` 等事件接口 |
| `NullTaskReporter` | `core_report` | 空实现的任务上报器，作为关闭上报功能时的占位对象 |
| `ReporterProtocol` | `core_report` | Reporter 依赖方所需的最小接口协议 |
| `TaskReporter` | `core_report` | 任务状态上报器，后台线程周期性向 `celestialflow-web` 服务推送运行状态并拉取控制指令 |

## 文件说明

### 核心组件

1. **core_observer.py** (`BaseObserver`)
   - **作用**: 执行器生命周期观察者基类
   - **关键功能**:
     - `BaseObserver`: 定义生命周期事件接口，子类按需覆写

2. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **作用**: 任务状态上报器及其空实现
   - **关键功能**:
     - **状态上报**: 周期性推送任务图的结构、拓扑、运行状态、错误信息
     - **任务注入**: 从 `celestialflow-web` 服务拉取待注入任务，动态插入到运行中的任务图
     - **参数调整**: 从 `celestialflow-web` 服务拉取配置，动态调整上报间隔等参数
     - **错误同步**: 基于 `event_id` 增量推送错误记录
   - **通信协议**: HTTP
   - **数据格式**: JSON

## 模块关联

### 内部关联
- `BaseObserver` 是观察者模式的基类
- `TaskReporter` 是独立的报告组件，设计为可插拔
- `NullTaskReporter` 提供了关闭上报时的安全占位

### 外部关联
- **与 Stage 模块**: `TaskExecutor` 内部 `TaskMetrics` 持有 `list[BaseObserver]`，通过 `add_observer()` / `remove_observer()` 管理观察者
- **与 Graph 模块**: `TaskReporter` 收集任务图的结构和拓扑信息
- **与 Persistence 模块**: 获取持久化的日志和错误数据，依赖 `LogInlet`

## 架构特点

### Observer 模式
- **多播**: `TaskExecutor` 内部的 `TaskMetrics` 维护 `list[BaseObserver]`，在计数变化与启停节点广播事件
- **同步分发**: 在 `add_success_count` / `add_fail_count` / `add_task_count` / `on_start` / `on_finish` 等方法中同步调用所有已注册观察者的对应回调
- **异常隔离**: 子类覆写的回调会被 `__init_subclass__` 自动包装，异常统一交给 `observer_error()` 兜底，不会逃逸到框架

### 双向通信（TaskReporter）
- **上行通道**: 状态数据上报到 celestialflow-web 服务
- **下行通道**: 控制指令从 celestialflow-web 服务下发到运行实例

### 容错设计
- 网络中断时的优雅降级，不影响主流程执行
- `NullTaskReporter` 作为关闭上报时的无开销占位

## 使用模式

### TaskReporter 使用
```python
from celestialflow.observability import TaskReporter

reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=my_task_graph,
)
reporter.start()
```

## 使用示例

### 自定义 Observer + TaskReporter 搭配使用

```python
from celestialflow import TaskGraph, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter


# 1. 自定义观察者：统计任务执行结果
class StatsObserver(BaseObserver):
    def __init__(self):
        self.success_count = 0
        self.fail_count = 0

    def on_task_success(self, count: int = 1):
        self.success_count += count

    def on_task_fail(self, count: int = 1):
        self.fail_count += count

    def on_finish(self):
        print(f"执行结束：成功 {self.success_count}，失败 {self.fail_count}")


# 2. 定义任务处理函数
def process_item(item: int) -> int:
    if item % 5 == 0:
        raise ValueError(f"跳过数字 {item}")
    return item * 2


# 创建任务图
graph = TaskGraph("ObsDemo")
stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
graph.set_stages([stage])

# 注册自定义观察者到 stage 的执行器
stats_observer = StatsObserver()
stage.add_observer(stats_observer)

# 可选：启用 TaskReporter 上报到 celestialflow-web 服务
reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=graph,
)
reporter.start()

# 启动任务图
graph.run({stage.get_name(): list(range(20))})

# 停止上报器
reporter.stop()

# 查看统计结果
print(
    f"最终统计 - 成功: {stats_observer.success_count}, 失败: {stats_observer.fail_count}"
)
```

此示例展示了可观测组件的协作：
- **自定义 Observer**: 继承 `BaseObserver` 并覆写事件方法收集统计信息
- **TaskGraph 集成**: 通过 `TaskStage` 内置的观察者列表注册自定义观察者
- **TaskReporter**: 将运行状态推送到 `celestialflow-web` 服务用于监控或控制
