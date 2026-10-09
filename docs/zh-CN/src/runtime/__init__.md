# src/celestialflow/runtime/__init__.py

> 📅 最后更新日期: 2026/10/09

Runtime 模块提供了 CelestialFlow 任务运行时的核心基础设施，包括任务信封（Envelope）、队列（Queue）等组件。

## 模块概述

Runtime 模块负责管理任务执行过程中的数据包装与队列通信。它不负责任务调度本身（调度由 Graph 模块负责），而是提供运行期基础组件供上层使用。

### 公开导出符号 (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # 任务信封
    TaskInQueue,  # 任务输入队列
    TaskOutQueue,  # 任务输出队列
)
```

`__all__ = ["TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

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

### 工具模块

3. **util_errors.py**
   - **作用**: 完整的异常定义体系
   - **涵盖**: 配置异常、图结构异常、运行时异常、外部服务异常、任务逻辑异常
   - 详细异常列表见 `util_errors.md`

4. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`NodeStatus`、`CTreeEvent`、`NodeMetrics`、`MetricsView`

5. **util_event.py**
   - **作用**: 事件客户端抽象接口和本地实现
   - **关键类**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

6. **util_constant.py**
   - **作用**: 运行时常量定义（如日志级别映射）

7. **util_config.py**
   - **作用**: 运行时配置加载（如从 pyproject.toml 读取日志级别、上报地址与上报开关）

8. **util_format.py**
   - **作用**: 通用格式化工具（字符串截断、表格渲染、按值聚类）

> 说明：指标（Metrics）与上报（Reporter）相关实现已从 Runtime 模块迁往 `observer` / `observability` 区域，Runtime 仅保留 `util_types` 中定义只读的指标快照类型（`NodeMetrics`）与视图协议（`MetricsView`）。

## 模块关联

### 内部关联
- `TaskInQueue`/`TaskOutQueue` 使用 `util_types` 中的 `TerminationSignal`/`TerminationIdPool`
- `TaskInQueue` 内部使用 `util_errors` 中的 `DuplicateNodeError`、`UnknownNodeError`、`TerminationMergeError`
- 所有错误通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Graph 模块**: `TaskGraph` 管理各类任务节点，使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Node 模块**: 节点对象收发数据时使用 `TaskEnvelope`、`TaskInQueue`/`TaskOutQueue`，并通过 `util_types` 中的 `MetricsView` 读取只读指标视图

## 使用示例

以下示例展示 runtime 模块各基本组件的使用方式。

```python
from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：创建和访问任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"任务数据: {envelope.get_task()}")
print(f"任务ID: {envelope.get_id()}")
```

```python
# 2. TaskInQueue / TaskOutQueue：队列通信
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

1. **队列通信**: 合理设置 `maxsize` 避免内存溢出
2. **多来源管理**: 通过 `add_source_name()` / `add_queue()` 防重地注册上游/下游通道
3. **终止合并**: 由 `TaskInQueue` 在集齐所有上游终止信号后合并为 `TerminationIdPool`