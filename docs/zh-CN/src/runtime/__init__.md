# Runtime 模块

> 📅 最后更新日期: 2026/05/24

Runtime 模块提供了 CelestialFlow 的任务执行运行时环境，包括任务调度、队列管理、错误处理、性能监控等核心功能。它是任务实际执行的基础设施层。

## 模块概述

Runtime 模块负责管理任务执行的生命周期，从任务提交到结果返回的整个过程。它提供了三种执行模式（串行 `serial`、线程 `thread`、异步 `async`）、健壮的错误处理机制、性能监控和资源管理功能。

## 文件说明

### 核心运行时组件

1. **core_dispatch.py** (`TaskDispatch`)
   - **作用**: 任务调度器，以串行、线程或异步方式执行单个任务
   - **执行模式**:
     - `dispatch_serial`: 顺序执行任务
     - `dispatch_thread`: 基于 `ThreadPoolExecutor` 并发执行任务
     - `dispatch_async`: 基于 `asyncio` 的异步任务（信号量控制并发数）
   - **关键功能**: 任务重试、去重检查、终止信号合并、线程池生命周期管理

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **作用**: 任务输入/输出队列，实现节点间的数据传递与终止信号合并
   - **队列类型**:
     - `TaskInQueue`: 任务输入队列，聚合多个上游来源的任务和终止信号
     - `TaskOutQueue`: 任务输出队列，将结果广播到一个或多个下游队列通道
   - **关键功能**: 终止信号合并、来源名称管理、日志记录、动态添加队列通道

3. **core_envelope.py** (`TaskEnvelope`)
   - **作用**: 任务数据包装器，封装原始任务及其哈希、ID、来源等元信息
   - **包含信息**: 任务数据、SHA1 哈希值（惰性计算）、任务 ID、来源标识、前驱任务引用
   - **关键功能**: 数据封装、惰性哈希计算、任务 ID 变更（重试场景）

### 监控和度量

4. **core_metrics.py** (`TaskMetrics`)
   - **作用**: 任务执行指标统计，管理成功/失败/重复计数和去重逻辑
   - **关键功能**: 线程安全计数器、重复任务检查、可重试异常配置、任务完成判断

### 工具和工具类

5. **util_errors.py**（异常类层级）
   - **作用**: 完整的异常定义体系
   - **涵盖**: 配置异常、图结构异常、运行时异常、外部服务异常、任务逻辑异常
   - 详细异常列表见 `util_errors.md`

6. **util_factories.py**
   - **作用**: 队列对象的工厂函数
   - **工厂函数**:
     - `make_task_in_queue()`: 创建 `TaskInQueue` 实例
     - `make_task_out_queue()`: 创建 `TaskOutQueue` 实例

7. **util_types.py**
   - **作用**: 运行时类型定义和数据结构
   - **包含类型**:
     - **核心信号**: `TerminationSignal` / `TERMINATION_SIGNAL` — 哨兵对象；`TerminationIdPool` — 终止信号 ID 池
     - **计数器**: `ValueWrapper` — 可选线程锁的整数包装器；`SumCounter` — 多 `ValueWrapper` 级联累加
     - **上下文管理器**: `NoOpContext` — 空上下文管理器，用于禁用 `with` 逻辑
     - **生命周期**: `StageStatus` — IntEnum（NOT_STARTED / RUNNING / STOPPED）
     - **事件常量**: `CTreeEvent` — 任务/终止事件名称常量（TASK_INPUT / TASK_SUCCESS / TASK_ERROR / TASK_RETRY_PREFIX / TASK_DUPLICATE / TERMINATION_INPUT / TERMINATION_MERGE）
     - **错误记录**: `PersistedErrorRecord` — 持久化错误记录 frozen dataclass（支持分组）
     - **可视化**: `STAGE_STYLE` — CelestialTree 节点标签样式

8. **util_hash.py**
   - **作用**: 对象哈希计算，用于任务去重
   - **关键函数**:
     - `make_hashable()`: 递归转换 list/dict/set 为稳定可哈希结构
     - `object_to_hash()`: pickle 后计算 SHA1，返回 `bytes`

9. **util_estimators.py**
   - **作用**: 执行时间估算和进度计算
   - **关键函数**:
     - `calc_remaining()`: 基于均值估算剩余时间
     - `calc_elapsed()`: 按状态累计已耗时间
     - `calc_global_remain_equal_pred()`: 基于 DAG 拓扑的全局剩余时间估算（偏保守）

## 模块关联

### 内部关联
- `TaskDispatch` 使用 `TaskInQueue`/`TaskOutQueue` 获取任务和发送结果
- `TaskEnvelope` 在队列中传递，携带任务的哈希和来源信息
- `TaskMetrics` 监控 `TaskDispatch` 的执行状态
- 所有错误通过 `CelestialFlowError` 及其子类统一处理

### 外部关联
- **与 Stage 模块**: `TaskDispatch` 执行 `TaskExecutor` 和 `TaskStage`
- **与 Graph 模块**: 为 `TaskGraph` 提供执行引擎和通信机制
- **与 Persistence 模块**: 支持执行状态持久化和日志记录
- **与 Observability 模块**: 提供监控数据和性能指标

## 架构特点

### 三模式执行
- `serial`: 顺序执行，适合轻量任务和调试
- `thread`: 线程池并发，适合 I/O 密集型任务
- `async`: 异步协程，适合网络 I/O 场景

### 健壮性设计
- 完整的错误处理链条（重试 / 不可重试）
- 线程安全计数器
- 资源泄漏防护（线程池自动释放）

### 可观测性
- 全面的指标收集（成功、失败、重复、待处理）
- 基于 DAG 的全局剩余时间估算
- 详细的执行日志

## 使用示例

以下示例展示 runtime 模块各组件协同使用的方式，涵盖任务信封、指标统计和队列通信。

```python
from queue import Queue as ThreadQueue
from celestialflow.runtime import TaskEnvelope, TaskMetrics, TaskInQueue, TaskOutQueue
from celestialflow.persistence import LogInlet

# 1. TaskEnvelope：创建和操作任务信封
envelope = TaskEnvelope(task={"data": 42}, id=1, source="input")
print(f"任务数据: {envelope.get_task()}")
print(f"任务哈希: {envelope.get_hash().hex()[:8]}...")
print(f"任务ID: {envelope.get_id()}")

# 重试时变更 ID
envelope.change_id(100)
print(f"变更后 ID: {envelope.get_id()}")
```

```python
# 2. TaskMetrics：指标统计
import time

metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)

# 模拟任务处理过程
metrics.add_task_count(5)
metrics.add_success_count(3)
metrics.add_error_count(1)
metrics.add_duplicate_count(1)

# 查询各项计数
print(f"输入: {metrics.get_task_count()}")
print(f"成功: {metrics.get_success_count()}")
print(f"失败: {metrics.get_error_count()}")
print(f"重复: {metrics.get_duplicate_count()}")
print(f"全部完成: {metrics.is_tasks_finished()}")

# 获取快照字典
counts = metrics.get_counts()
print(f"待处理: {counts['tasks_pending']}")
```

```python
# 3. TaskInQueue / TaskOutQueue：队列通信
from celestialflow.runtime.util_errors import ConfigurationError

class FakeLogInlet:
    """简化日志入口，仅用于演示"""
    def put_item(self, t, id, source, out_name): pass
    def put_item_error(self, source, out_name, e): pass
    def get_item(self, t, id, source, out_name): pass

log_inlet = FakeLogInlet()

# 创建输入队列（聚合上游任务）
in_queue = TaskInQueue(
    queue=ThreadQueue(),
    source_names=["producer"],
    out_name="processor",
    log_inlet=log_inlet,
)

# 创建输出队列（广播到下游）
out_queue = TaskOutQueue(
    queue_list=[ThreadQueue()],
    target_names=["consumer"],
    in_name="processor",
    log_inlet=log_inlet,
)

# 上游生产任务
envelope_a = TaskEnvelope(task="hello", id=1, source="producer")
in_queue.put(envelope_a)

# 下游消费任务
retrieved = in_queue.get()
print(f"出队任务: {retrieved.get_task()}")

# 输出队列广播任务
out_queue.put(envelope_a)

# 动态添加输出通道
out_queue.add_queue(ThreadQueue(), "another_consumer")
print(f"输出通道数: {len(out_queue.queue_list)}")
```

## 最佳实践

1. **I/O 密集型任务**: 使用 `thread` 模式
2. **异步任务**: 使用 `async` 模式（函数需为协程）
3. **调试**: 使用 `serial` 模式，便于追踪单次执行
4. **关键任务**: 配置适当的 `max_retries` 和 `add_retry_exceptions`
5. **重复敏感场景**: 开启 `enable_duplicate_check=True`
