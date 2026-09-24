# src/celestialflow/runtime/__init__.py

> 📅 Last Updated: 2026/09/24

The Runtime module provides the core infrastructure for CelestialFlow task execution, including task envelopes (`Envelope`), queues (`Queue`), metrics (`Metrics`), and other components.

## Module Overview

The Runtime module is responsible for managing data packaging, queue communication, and metrics tracking during task execution. It is not responsible for task scheduling itself (scheduling is handled by the Graph module), but rather provides fundamental runtime components for upper layers.

### Publicly Exported Symbols (`__all__`)

```python
from celestialflow.runtime import (
    TaskEnvelope,  # Task envelope
    TaskInQueue,  # Task input queue
    TaskMetrics,  # Task metrics
    TaskOutQueue,  # Task output queue
)
```

> **Note**: Symbols from utility modules such as `util_constant`, `util_errors`, `util_event`, `util_types`, `util_config`, `util_format` are **not** in `runtime/__init__.py`'s `__all__` and must be imported via their full paths (e.g., `from celestialflow.runtime.util_errors import ConfigurationError`).

## File Descriptions

### Core Runtime Components

1. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues, implementing data transfer between nodes and termination signal merging
   - **Queue types**:
     - `TaskInQueue`: Task input queue, aggregating tasks and termination signals from multiple upstream sources
     - `TaskOutQueue`: Task output queue, broadcasting results to one or more downstream queue channels
   - **Key Features**: Termination signal merging, source name management, dynamic queue channel addition

2. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper, encapsulating the raw task and its ID
   - **Contained Information**: Task data (`_task`), task ID (`_id`)
   - **Key Features**: Data encapsulation and access

3. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics, managing external injection / upstream reception / success / failure / duplicate counts
   - **Key Features**: Thread-safe counters, per-node upstream/downstream counting, observer callbacks, retryable exception configuration, task completion determination, measured busy duration

### Utility Modules

4. **util_errors.py**
   - **Purpose**: Complete exception definition system
   - **Coverage**: Configuration errors, graph structure errors, runtime errors, external service errors, task logic errors
   - See `util_errors.md` for detailed exception list

5. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Contained types**: `TerminationSignal`, `TERMINATION_SIGNAL`, `TerminationIdPool`, `NoOpContext`, `ValueWrapper`, `StageStatus`, `CTreeEvent`

6. **util_event.py**
   - **Purpose**: Event client abstract interface and local implementation
   - **Key Classes**: `EventClient` (Protocol), `LocalEventClient`, `clone_event_client()`

7. **util_constant.py**
   - **Purpose**: Runtime constant definitions (e.g., log level mapping)

8. **util_config.py**
   - **Purpose**: Runtime configuration loading (e.g., reading log level from `pyproject.toml`)

9. **util_format.py**
   - **Purpose**: General formatting utilities (string truncation, table rendering, clustering by value)

## Module Relationships

### Internal Relationships
- `TaskInQueue`/`TaskOutQueue` use `TerminationSignal`/`TerminationIdPool` from `util_types`
- `TaskMetrics` uses `ValueWrapper` from `util_types`, and expresses lifecycle states via `StageStatus`
- All errors are uniformly handled via `CelestialFlowError` and its subclasses

### External Relationships
- **With Graph Module**: `TaskGraph` manages `TaskExecutor` / `TaskSplitter` / `TaskRouter` and other nodes, using `TaskInQueue`/`TaskOutQueue` as inter-node communication pipes
- **With Node Module**: Node objects (`BaseTaskNode` and its subclasses) hold `TaskMetrics` and use `TaskInQueue`/`TaskOutQueue` for data transfer

## Usage Examples

The following examples demonstrate the usage of basic components in the runtime module.

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

## Best Practices

1. **Critical tasks**: Configure retryable exception types via `set_retry_exceptions()`
2. **Per-node statistics**: Use `set_upstream_counter()` / `set_downstream_counter()` to track inter-node traffic
3. **Queue communication**: Properly set `maxsize` to avoid memory overflow
