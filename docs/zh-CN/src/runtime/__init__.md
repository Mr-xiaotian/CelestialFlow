# src/celestialflow/runtime/__init__.py

> 📅 最后更新日期: 2026/09/24

Runtime 模块提供了 CelestialFlow 任务运行时的核心基础设施，包括任务信封（Envelope）、队列（Queue）、指标统计（Metrics）等组件。

## 模块概述

Runtime 模块负责管理任务执行过程中的数据包装、队列通信和指标统计。它不负责任务调度本身（调度由 Graph 模块负责），而是提供运行期基础组件供上层使用。

### 公开导出符号 (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # 任务信封
    TaskInQueue,  # 任务输入队列
    TaskMetrics,  # 任务指标统计
    TaskOutQueue,  # 任务输出队列
)
```

`__all__ = ["TaskEnvelope", "TaskInQueue", "TaskMetrics", "TaskOutQueue"]`

> **注意**：`util_constant`、`util_errors`、`util_event`、`util_types`、`util_config`、`util_format` 等工具模块的符号**不在** `runtime/__init__.py` 的 `__all__` 中，需要通过完整路径导入（如 `from celestialflow.runtime.util_errors import ConfigurationError`）。

## 文件说明

### 核心运行时组件

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **作用**: 任务输入/输出队列，实现节点间的数据传递与终止信号合并
   - **队列类型**:
     - `TaskInQueue`: 任务输入队列，聚合多个上游来源的任务和终止信号
     - `TaskOutQueue`: 任务输出队列，将结果广播到一个或多个下游队列通道
   - **关键功能**: 终止信号合并、来源名称管理、动态添加队列通道

2. **core_envelope.py** (`TaskEnvelope`)
   - **作用**: 任务数据包装器，封装原始任务及其 ID
   - **包含信息**: 任务数据（`_task`）、任务 ID（`_id`）
   - **关键功能**: 数据封装与访问

3. **core_metrics.py** (`TaskMetrics`)
   - **作用**: 任务执行指标统计，管理外部注入/上游接收/成功/失败/重复计数
   - **关键功能**: 线程安全计数器、上游/下游分节点计数、观察者回调、可重试异常配置、任务完成判断、实测忙碌耗时

### 工具模块

4. **util_errors.py**
   - **作用**: 完整的异常定义体系
   - **涵盖**: 配置异常、图结构异常、运行时异常、外部服务异常、任务逻辑异常
   - 详细异常列表见 `util_errors.md`

5. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`StageStatus`、`CTreeEvent`

6. **util_event.py**
   - **作用**: 事件客户端抽象接口和本地实现
   - **关键类**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

7. **util_constant.py**
   - **作用**: 运行时常量定义（如日志级别映射）

8. **util_config.py**
   - **作用**: 运行时配置加载（如从 pyproject.toml 读取日志级别）

9. **util_format.py**
   - **作用**: 通用格式化工具（字符串截断、表格渲染、按值聚类）

## 模块关联

### 内部关联
- `TaskInQueue`/`TaskOutQueue` 使用 `util_types` 中的 `TerminationSignal`/`TerminationIdPool`
- `TaskMetrics` 使用 `util_types` 中的 `ValueWrapper`，并通过 `StageStatus` 表达生命周期状态
- 所有错误通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Graph 模块**: `TaskGraph` 管理 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 等节点，使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Node 模块**: 节点对象（`BaseTaskNode` 及其子类）持有 `TaskMetrics`，并使用 `TaskInQueue`/`TaskOutQueue` 收发数据

## 使用示例

以下示例展示 runtime 模块各基本组件的使用方式。

```python
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：创建和访问任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"任务数据: {envelope.get_task()}")
print(f"任务ID: {envelope.get_id()}")
```

```python
from celestialflow.runtime import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper

# 2. TaskMetrics：指标统计
metrics = TaskMetrics()

# 模拟任务处理过程：外部注入 3 个 + 上游接收 2 个
metrics.add_external_input_count(3)
metrics.set_upstream_counter("upstream", ValueWrapper(value=2))
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 查询各项计数
print(f"输入: {metrics.get_input_count()}")  # 5
print(f"成功: {metrics.get_success_count()}")  # 3
print(f"失败: {metrics.get_fail_count()}")  # 1
print(f"重复: {metrics.get_duplicate_count()}")  # 1
print(f"全部完成: {metrics.is_tasks_finished()}")

# 获取快照字典
counts = metrics.get_counts()
print(f"待处理: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：队列通信
from queue import Queue as ThreadQueue

# 创建输入队列
in_queue = TaskInQueue(out_name="processor")
in_queue.add_source_name("producer")

# 创建输出队列
out_queue = TaskOutQueue(in_name="processor")
consumer_queue = ThreadQueue()
out_queue.add_queue("consumer", consumer_queue)

# 生产任务
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# 消费任务
retrieved = in_queue.get()
print(f"出队任务: {retrieved.get_task()}")
```

## 最佳实践

1. **关键任务**: 通过 `set_retry_exceptions()` 配置可重试异常类型
2. **分节点统计**: 使用 `set_upstream_counter()` / `set_downstream_counter()` 追踪节点间流量
3. **队列通信**: 合理设置 `maxsize` 避免内存溢出
