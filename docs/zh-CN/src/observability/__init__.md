# Observability 模块

> 📅 最后更新日期: 2026/05/24

Observability 模块提供了 CelestialFlow 的可观测性功能，包括运行状态监控、性能指标收集、错误追踪和远程控制。它使任务执行过程变得透明、可监控和可控制。

## 模块概述

Observability 模块负责收集、聚合和上报系统的运行状态，提供实时的监控视图和远程控制能力。通过该模块，用户可以实时了解任务执行状态、性能指标和错误信息，并能够动态调整系统行为。

## 导出项

| 导出符号 | 来源模块 | 说明 |
|---------|---------|------|
| `BaseObserver` | `core_observer` | 执行器生命周期观察者基类，定义 `on_start`, `on_task_success`, `on_task_fail`, `on_task_duplicate`, `on_tasks_added`, `on_finish` 等事件接口 |
| `CallbackObserver` | `core_observer` | 通过关键字参数传入回调函数的观察者实现，无需定义子类 |
| `TaskReporter` | `core_report` | 任务状态上报器，后台线程周期性向 Web 服务器推送运行状态并拉取控制指令 |
| `NullTaskReporter` | `core_report` | 空实现的任务上报器，作为关闭上报功能时的占位对象，`start()` / `stop()` 均为空操作 |
| `TaskProgress` | `core_progress` | 基于 `tqdm` 的任务进度可视化工具，继承自 `BaseObserver`，自动在终端显示进度条 |

## 文件说明

### 核心组件

1. **core_observer.py** (`BaseObserver`, `CallbackObserver`)
   - **作用**: 执行器生命周期观察者基类与回调式观察者
   - **关键功能**:
     - `BaseObserver`: 定义生命周期事件接口（`on_start`、`on_task_success`、`on_task_fail`、`on_task_duplicate`、`on_tasks_added`、`on_finish`），子类按需覆写
     - `CallbackObserver`: 通过关键字参数传入回调函数，无需定义子类

2. **core_report.py** (`TaskReporter`, `NullTaskReporter`)
   - **作用**: 任务状态上报器及其空实现
   - **关键功能**:
     - **状态上报**: 周期性推送任务图的结构、拓扑、运行状态、错误信息
     - **任务注入**: 从 Web UI 接收用户注入的新任务，动态插入到运行中的任务图
     - **参数调整**: 从服务器拉取配置，动态调整上报间隔等参数
     - **错误同步**: 支持两种错误推送模式（元数据模式和内容模式）
     - **NullTaskReporter**: 关闭上报功能时的占位对象，不发起任何网络请求
   - **通信协议**: HTTP
   - **数据格式**: JSON

3. **core_progress.py** (`TaskProgress`)
   - **作用**: 基于 `tqdm` 的任务进度可视化，继承 `BaseObserver`
   - **关键功能**:
     - 通过 `on_start` 创建进度条
     - 通过 `on_task_success/fail/duplicate` 更新进度
     - 通过 `on_tasks_added` 动态增加总任务数
     - 通过 `on_finish` 关闭进度条

## 模块关联

### 内部关联
- `BaseObserver` 是观察者模式的基类，`TaskProgress` 和 `CallbackObserver` 均基于它实现
- `TaskReporter` 是独立的报告组件，设计为可插拔
- `NullTaskReporter` 提供了关闭上报时的安全占位

### 外部关联
- **与 Stage 模块**: `TaskExecutor` 持有 `list[BaseObserver]`，通过 `add_observer()` / `remove_observer()` 管理观察者
- **与 Graph 模块**: 收集任务图的结构和拓扑信息
- **与 Runtime 模块**: 收集执行状态、性能指标和错误信息
- **与 Persistence 模块**: 获取持久化的日志和错误数据
- **与 Web 模块**: 与 Web UI 进行双向通信，支持状态展示和远程控制

## 架构特点

### Observer 模式
- **多播**: `TaskExecutor` 内部维护 `list[BaseObserver]`，在生命周期节点广播事件
- **同步分发**: 事件通过 `_notify(method_name, *args, **kwargs)` 同步调用所有观察者
- **空列表等效 Null**: 当 observer 列表为空时，无任何开销

### 双向通信（TaskReporter）
- **上行通道**: 状态数据上报到 Web 服务器
- **下行通道**: 控制指令从 Web 服务器下发到运行实例
- **实时性**: 支持实时状态更新和即时控制

### 容错设计
- 网络中断时的优雅降级，不影响主流程执行
- `NullTaskReporter` 作为关闭上报时的无开销占位

## 使用模式

### Observer 使用
```python
from celestialflow import TaskExecutor, TaskProgress, CallbackObserver

# 使用 TaskProgress 显示进度条
executor = TaskExecutor("Test", my_func)
executor.add_observer(TaskProgress())
executor.start(tasks)

# 使用 CallbackObserver 自定义行为
observer = CallbackObserver(
    on_task_success=lambda count=1: print(f"成功: {count}"),
    on_finish=lambda: print("完成"),
)
executor.add_observer(observer)
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
