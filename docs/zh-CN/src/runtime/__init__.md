# Runtime 模块

> 📅 最后更新日期: 2026/08/12

Runtime 模块提供了 CelestialFlow 任务运行时的核心基础设施，包括任务信封（Envelope）、队列（Queue）、指标统计（Metrics）等组件。

## 模块概述

Runtime 模块负责管理任务执行过程中的数据包装、队列通信和指标统计。它不负责任务调度本身（调度由 Stage 模块负责），而是提供运行期基础组件供上层使用。

### 公开导出符号 (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # 任务信封
    TaskInQueue,  # 任务输入队列
    TaskMetrics,  # 任务指标统计
    TaskOutQueue,  # 任务输出队列
)
```

> **注意**：`util_constant`、`util_errors`、`util_estimators`、`util_event`、`util_hash`、`util_types`、`util_config`、`util_format` 等工具模块的符号**不在** `runtime/__init__.py` 的 `__all__` 中，需要通过完整路径导入（如 `from celestialflow.runtime.util_errors import ConfigurationError`）。

## 文件说明

### 核心运行时组件

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **作用**: 任务输入/输出队列，实现节点间的数据传递与终止信号合并
   - **队列类型**:
     - `TaskInQueue`: 任务输入队列，聚合多个上游来源的任务和终止信号
     - `TaskOutQueue`: 任务输出队列，将结果广播到一个或多个下游队列通道
   - **关键功能**: 终止信号合并、来源名称管理、动态添加队列通道

2. **core_envelope.py** (`TaskEnvelope`)
   - **作用**: 任务数据包装器，封装原始任务及其哈希、ID 等元信息
   - **包含信息**: 任务数据、SHA1 哈希值（惰性计算）、任务 ID
   - **关键功能**: 数据封装、惰性哈希计算、不可 hash 任务兜底

3. **core_metrics.py** (`TaskMetrics`)
   - **作用**: 任务执行指标统计，管理成功/失败/重复计数和去重逻辑
   - **关键功能**: 线程安全计数器、重复任务检查、可重试异常配置、任务完成判断

### 工具模块

4. **util_errors.py**
   - **作用**: 完整的异常定义体系
   - **涵盖**: 配置异常、图结构异常、运行时异常、外部服务异常、任务逻辑异常
   - 详细异常列表见 `util_errors.md`

5. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**: `TerminationSignal`、`TerminationIdPool`、`ValueWrapper`、`SumCounter`、`NoOpContext`、`StageStatus`、`CTreeEvent`

6. **util_hash.py**
   - **作用**: 对象哈希计算，用于任务去重
   - **关键函数**: `make_hashable()`、`object_to_hash()`

7. **util_estimators.py**
   - **作用**: 执行时间估算和进度计算
   - **关键函数**: `calc_remaining()`、`calc_elapsed()`、`format_avg_time()`

8. **util_event.py**
   - **作用**: 事件客户端抽象接口和本地实现
   - **关键类**: `EventClient`（Protocol）、`LocalEventClient`、`clone_event_client()`

9. **util_constant.py**
   - **作用**: 运行时常量定义（如日志级别映射）

10. **util_config.py**
    - **作用**: 运行时配置加载（如从 pyproject.toml 读取日志级别）

11. **util_format.py**
    - **作用**: 通用格式化工具（字符串截断、表格渲染、时间格式化等）

## 模块关联

### 内部关联
- `TaskEnvelope` 使用 `util_hash` 计算任务哈希
- `TaskInQueue`/`TaskOutQueue` 使用 `util_types` 中的 `TerminationSignal`/`TerminationIdPool`
- `TaskMetrics` 使用 `util_types` 中的 `ValueWrapper`/`SumCounter`
- 所有错误通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Stage 模块**: Stage 使用 `TaskInQueue`/`TaskOutQueue` 作为节点间通信管道
- **与 Graph 模块**: 为 `TaskGraph` 提供队列和指标基础设施

## 使用示例

以下示例展示 runtime 模块各基本组件的使用方式。

```python
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue

# 1. TaskEnvelope：创建和操作任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1)
print(f"任务数据: {envelope.get_task()}")
print(f"任务哈希: {envelope.get_hash().hex()[:8]}...")
print(f"任务ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics：指标统计
metrics = TaskMetrics(enable_duplicate_check=True)

# 模拟任务处理过程
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_fail_count(1)
metrics.add_duplicate_count(1)

# 查询各项计数
print(f"输入: {metrics.get_task_count()}")
print(f"成功: {metrics.get_success_count()}")
print(f"失败: {metrics.get_fail_count()}")
print(f"重复: {metrics.get_duplicate_count()}")
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
out_queue.add_queue(consumer_queue, "consumer")

# 生产任务
envelope_a = TaskEnvelope(task="hello", id=1)
in_queue.put(envelope_a)
out_queue.put(envelope_a)

# 消费任务
retrieved = in_queue.get()
print(f"出队任务: {retrieved.get_task()}")
```

## 最佳实践

1. **关键任务**: 配置适当的 `set_retry_exceptions`
2. **重复敏感场景**: 开启 `enable_duplicate_check=True`
3. **队列通信**: 合理设置 `maxsize` 避免内存溢出
