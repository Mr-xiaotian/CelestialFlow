# src/celestialflow/runtime/__init__.py

> 📅 最后更新日期: 2026/10/30

Runtime 模块提供了 CelestialFlow 任务运行时的核心基础设施，包括运行期配置（`ReportConfig`）、任务信封（Envelope）与队列（Queue）等组件。

## 模块概述

Runtime 模块负责管理任务执行过程中的数据包装、队列通信与运行期配置类型。它不负责任务调度本身（调度由 Graph 模块负责），而是提供运行期基础组件供上层使用。

### 公开导出符号 (`__all__`)

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,  # 默认上报地址常量
    ReportConfig,  # 远程上报配置（frozen 配置对象）
    TaskEnvelope,  # 任务信封
    TaskInQueue,  # 任务输入队列
    TaskOutQueue,  # 任务输出队列
)
```

`__all__ = ["DEFAULT_REPORT_URL", "ReportConfig", "TaskEnvelope", "TaskInQueue", "TaskOutQueue"]`

> **注意**：只有 `core_*` 文件中的符号会被导出。`util_constant`、`util_errors`、`util_event`、`util_format`、`util_log_level`、`util_types` 等 `util_*` 模块的符号**不在** `runtime/__init__.py` 的 `__all__` 中，需要通过完整路径导入（如 `from celestialflow.runtime.util_errors import ConfigurationError`、`from celestialflow.runtime.util_log_level import normalize_log_level`）。

## 文件说明

### 核心运行时组件

1. **core_config.py** (`DEFAULT_REPORT_URL`, `ReportConfig`)
   - **作用**: 定义运行入口显式传入的上报配置；`report=ReportConfig(...)` 启用上报，`report=None` 关闭上报
   - **关键功能**: 默认地址常量、构造期地址校验（`http`/`https`）、去掉尾部 `/` 的规范化
   - 详见 `core_config.md`

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **作用**: 任务输入/输出队列，实现节点间的数据传递与终止信号合并
   - **队列类型**:
     - `TaskInQueue`: 任务输入队列，聚合多个上游来源的任务和终止信号
     - `TaskOutQueue`: 任务输出队列，将结果广播到一个或多个下游队列通道
   - **关键功能**: 终止信号合并、来源名称管理、动态添加队列通道

3. **core_envelope.py** (`TaskEnvelope`)
   - **作用**: 任务数据包装器，封装原始任务及其 ID
   - **包含信息**: 任务数据（`_task`）、任务 ID（`_id`）
   - **关键功能**: 数据封装与访问

### 工具模块（不对外导出）

4. **util_errors.py**
   - **作用**: 完整的异常定义体系
   - **涵盖**: 配置异常、图结构异常、运行时异常、外部服务异常、任务逻辑异常
   - 详细异常列表见 `util_errors.md`

5. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**: `TerminationSignal`、`TERMINATION_SIGNAL`、`TerminationIdPool`、`NoOpContext`、`ValueWrapper`、`NodeStatus`、`CTreeEvent`、`NodeMetrics`、`MetricsView`

6. **util_event.py**
   - **作用**: 事件客户端抽象接口和本地实现
   - **关键类**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

7. **util_constant.py**
   - **作用**: 运行时常量定义（日志级别映射表 `LEVEL_DICT`）

8. **util_log_level.py**
   - **作用**: 日志级别默认值 `DEFAULT_LOG_LEVEL` 与规范化校验 `normalize_log_level()`（仅供运行入口内部使用）

9. **util_format.py**
   - **作用**: 通用格式化工具（字符串截断、表格渲染、按值聚类）

> 说明：指标（Metrics）与上报（Reporter）相关实现位于 `observer` / `reporter` 区域，Runtime 仅保留 `util_types` 中定义只读的指标快照类型（`NodeMetrics`）与视图协议（`MetricsView`），以及 `core_config` 中的上报**配置对象**（不包含上报执行逻辑）。

## 模块关联

### 内部关联
- `core_queue` 使用 `util_types` 中的 `TerminationSignal`/`TerminationIdPool`
- `core_queue` 使用 `util_errors` 中的 `DuplicateNodeError`、`UnknownNodeError`、`TerminationMergeError`
- `core_config` 使用 `util_errors` 中的 `ConfigurationError`
- `util_log_level` 使用 `util_constant` 的 `LEVEL_DICT` 与 `util_errors` 的 `ConfigurationError` / `InvalidOptionError`
- 所有错误通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Graph 模块**: `TaskGraph.run()` / `run_async()` / `restore_db()` 的 `report` 参数类型即 `ReportConfig`；`TaskGraph` 使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Assembly 模块**: `run_graph_resources()` 依据 `report` 是否为 `None` 决定是否装配远程上报资源
- **与 Node 模块**: 节点对象收发数据时使用 `TaskEnvelope`、`TaskInQueue`/`TaskOutQueue`，并通过 `util_types` 中的 `MetricsView` 读取只读指标视图
- **与包根**: `celestialflow/__init__.py` 重新导出 `ReportConfig`（`from celestialflow import ReportConfig`）

## 使用示例

以下示例展示 runtime 模块各基本组件的使用方式。

```python
from celestialflow.runtime import (
    DEFAULT_REPORT_URL,
    ReportConfig,
    TaskEnvelope,
    TaskInQueue,
    TaskOutQueue,
)

# 1. ReportConfig：上报配置
config = ReportConfig()  # 使用默认地址
print(f"上报地址: {config.url}")  # http://127.0.0.1:5005
print(f"默认地址常量: {DEFAULT_REPORT_URL}")

custom = ReportConfig("https://flow.example.com/api/")
print(f"规范化后: {custom.url}")  # https://flow.example.com/api

# 2. TaskEnvelope：创建和访问任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"任务数据: {envelope.get_task()}")
print(f"任务ID: {envelope.get_id()}")
```

```python
# 3. TaskInQueue / TaskOutQueue：队列通信
from queue import Queue as ThreadQueue

from celestialflow.runtime import TaskEnvelope, TaskInQueue, TaskOutQueue

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
print(f"下游收到: {consumer_queue.get().get_task()}")
```

```python
# 4. 把 ReportConfig 传给图运行入口
from celestialflow import TaskExecutor, TaskGraph

from celestialflow.runtime import ReportConfig

graph = TaskGraph(name="RuntimeDemo")
graph.set_nodes([TaskExecutor("worker", lambda x: x * 2)])
graph.run({"worker": [1, 2, 3]}, report=ReportConfig())
```

## 最佳实践

1. **上报开关**: 想上报就构造 `ReportConfig` 传入 `report=`，不想上报就保持默认 `None`；不存在从 `pyproject.toml` 隐式读取的行为
2. **队列通信**: 合理设置 `maxsize` 避免内存溢出
3. **多来源管理**: 通过 `add_source_name()` / `add_queue()` 防重地注册上游/下游通道
4. **终止合并**: 由 `TaskInQueue` 在集齐所有上游终止信号后合并为 `TerminationIdPool`
