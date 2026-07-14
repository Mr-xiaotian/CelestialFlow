# Observability 模块

> 📅 最后更新日期: 2026/06/22

Observability 模块提供了 CelestialFlow 的可观测性功能，包括运行状态监控、进度可视化、Observer 模式和远程状态上报。它使任务执行过程变得透明、可监控。

## 导出符号

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `BaseObserver` | `core_observer` | 执行器生命周期观察者基类，定义 `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` 等事件接口 |
| `TaskProgress` | `core_progress` | 基于 `tqdm` 的任务进度可视化工具，继承自 `BaseObserver` |
| `TaskReporter` | `core_report` | 任务状态上报器，后台线程周期性向 `celestialflow-web` 服务推送运行状态并拉取控制指令 |
| `NullTaskReporter` | `core_report` | 空实现的任务上报器，作为关闭上报功能时的占位对象 |

## 文件说明

### 核心组件

1. **core_observer.py** (`BaseObserver`)
   - **作用**: 执行器生命周期观察者基类
   - **关键功能**:
     - `BaseObserver`: 定义生命周期事件接口，子类按需覆写

2. **core_progress.py** (`TaskProgress`)
   - **作用**: 基于 `tqdm` 的任务进度可视化，继承 `BaseObserver`
   - **关键功能**:
     - 通过 `on_start` 创建进度条
     - 通过 `on_task_success/fail/duplicate` 更新进度
     - 通过 `on_tasks_added` 动态增加总任务数
     - 通过 `on_finish` 关闭进度条

3. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
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
- `BaseObserver` 是观察者模式的基类，`TaskProgress` 基于它实现
- `TaskReporter` 是独立的报告组件，设计为可插拔
- `NullTaskReporter` 提供了关闭上报时的安全占位

### 外部关联
- **与 Stage 模块**: `TaskExecutor` 持有 `list[BaseObserver]`，通过 `add_observer()` / `remove_observer()` 管理观察者
- **与 Graph 模块**: `TaskReporter` 收集任务图的结构和拓扑信息
- **与 Persistence 模块**: 获取持久化的日志和错误数据，依赖 `LogInlet`

## 架构特点

### Observer 模式
- **多播**: `TaskExecutor` 内部维护 `list[BaseObserver]`，在生命周期节点广播事件
- **同步分发**: 事件通过 `_notify(method_name, *args, **kwargs)` 同步调用所有观察者
- **空列表等效 Null**: 当 observer 列表为空时，无任何开销

### 双向通信（TaskReporter）
- **上行通道**: 状态数据上报到celestialflow-web服务
- **下行通道**: 控制指令从celestialflow-web服务下发到运行实例

### 容错设计
- 网络中断时的优雅降级，不影响主流程执行
- `NullTaskReporter` 作为关闭上报时的无开销占位

## 使用模式

### Observer 使用
```python
from celestialflow import TaskExecutor, TaskProgress

# 使用 TaskProgress 显示进度条
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)
```

### TaskReporter 使用
```python
from celestialflow.observability import TaskReporter

reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=my_task_graph,
    log_inlet=log_inlet,
)
reporter.start()
```

## 使用示例

### 自定义 Observer + TaskReporter 搭配使用

```python
from celestialflow import TaskGraph, TaskStage, BaseObserver
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

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
graph = TaskGraph(schedule_mode="eager")
stage = TaskStage("Processor", process_item, execution_mode="thread", max_workers=4)
graph.set_stages([stage])

# 注册自定义观察者到 stage 的执行器
stats_observer = StatsObserver()
stage.add_observer(stats_observer)

# 可选：启用 TaskReporter 上报到celestialflow-web服务
log_inlet = stage.log_inlet
reporter = TaskReporter(
    host="127.0.0.1",
    port=5000,
    task_graph=graph,
    log_inlet=log_inlet,
)
reporter.start()

# 启动任务图
graph.start_graph({stage.get_name(): list(range(20))})

# 停止上报器
reporter.stop()

# 查看统计结果
print(f"最终统计 - 成功: {stats_observer.success_count}, 失败: {stats_observer.fail_count}")
```

此示例展示了三类可观测组件的协作：
- **自定义 Observer**: 继承 `BaseObserver` 并覆写事件方法收集统计信息
- **TaskGraph 集成**: 通过 `TaskStage` 内置的观察者列表注册自定义观察者
- **TaskReporter**: 将运行状态推送到 `celestialflow-web` 服务用于监控或控制
