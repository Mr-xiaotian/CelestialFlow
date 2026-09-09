# node/core_node.py

> 📅 最后更新日期: 2026/09/09

`core_node.py` 定义了 CelestialFlow 节点层的核心基类 `BaseTaskNode[T, R]`。它负责把"队列通信 / 任务调度 / 指标统计 / 事件追踪 / 持久化日志 / 观察者回调"等运行期关注点集中到一个对象中，并暴露 `run` / `start` 等入口方法给上层 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 复用。

> ⚠️ `BaseTaskNode` 是**内部基类**，**不作为公共 API 导出**。仅 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 三个节点类是用户可见的。

## 核心对象

### `BaseTaskNode[T, R]`

| 字段 | 类型 | 说明 |
|------|------|------|
| `dispatch` | `TaskDispatch[T, R]` | 任务调度器（内部组件），由 `__init__` 创建 |
| `task_queue` | `TaskInQueue[T]` | 输入任务队列 |
| `result_queue` | `TaskOutQueue[R]` | 输出结果队列 |
| `metrics` | `TaskMetrics` | 任务指标统计对象（成功 / 失败 / 重复 / 耗时） |
| `ctree_client` | `EventClient` | 事件客户端（ctree），默认 `LocalEventClient()` |
| `func` | `Callable[[T], R]` 或 `Callable[[T], Awaitable[R]]` | 实际执行任务的回调 |
| `execution_mode` | `str` | `'serial'` / `'thread'` / `'async'` |
| `max_workers` | `int` | 最大并发工作数（默认 `min(32, cpu_count+4)`） |
| `max_retries` | `int` | 单任务最大重试次数（`1` 表示"原始一次 + 重试一次"） |
| `max_queue_size` | `int` | 输入队列容量上限（`0` 表示无界） |
| `max_info` | `int` | 日志中每条任务字符串的最大长度（默认 `50`） |
| `enable_duplicate_check` | `bool` | 是否启用基于任务哈希的重复检查 |
| `_name` | `str` | 节点 / 管理器名称 |
| `start_time` | `float` | 最近一次 `start` 的 `time.time()` 记录 |

```mermaid
classDiagram
    class BaseTaskNode {
        +TaskDispatch dispatch
        +TaskInQueue task_queue
        +TaskOutQueue result_queue
        +TaskMetrics metrics
        +EventClient ctree_client
        +Callable func
        +str execution_mode
        +int max_workers
        +int max_retries
        +int max_queue_size
        +int max_info
        +bool enable_duplicate_check
        +set_execution_mode(mode)
        +set_retry_exceptions(*exceptions)
        +set_ctree(client)
        +add_observer(observer)
        +remove_observer(observer)
        +put_task(task)
        +put_signal()
        +run(task_source)
        +run_async(task_source)
        +restore_db(db_path)
        +start()
        +start_async()
        +get_binding_counter(downstream_name)*
        +process_task_success(envelope, result, start_time)*
    }
```

## 初始化

```python
def __init__(
    self,
    name: str,
    func: Callable[[T], R] | Callable[[T], Awaitable[R]],
    *,
    execution_mode: str = "serial",
    max_workers: int | None = None,
    max_retries: int = 1,
    max_queue_size: int = 0,
    max_info: int = 50,
    enable_duplicate_check: bool = False,
):
    ...
```

`__init__` 的关键行为：

1. 通过 `set_name` 写入名称；
2. `_set_func` 校验回调签名（必须只接受 1 个位置参数），否则抛 `ConfigurationError`；
3. `set_execution_mode` 校验模式合法性；若 `execution_mode == "async"` 但 `func` 不是 `iscoroutinefunction`，抛 `ConfigurationError`；
4. 初始化 `max_workers / max_retries / max_queue_size / max_info / enable_duplicate_check`；
5. 默认安装 `LocalEventClient()`，可通过后续 `set_ctree(...)` 替换；
6. 实例化 `TaskDispatch(cast(BaseTaskNode[T, R], self), self.func, self.max_workers)`，并新建 `TaskInQueue` / `TaskOutQueue` / `TaskMetrics`。

## 配置 setter

| 方法 | 作用 | 抛错 |
|------|------|------|
| `set_name(name)` | 写入节点 / 管理器名称 | — |
| `set_execution_mode(execution_mode)` | 切换 `'serial'` / `'thread'` / `'async'` | `InvalidOptionError`（模式非法）、`ConfigurationError`（`async` 但 `func` 非协程） |
| `set_ctree(ctree_client)` | 替换事件客户端 | — |
| `set_retry_exceptions(*exceptions)` | 向 `metrics` 注册可重试的异常类型 | — |
| `add_observer(observer)` / `remove_observer(observer)` | 注册 / 解绑 `BaseObserver` | — |
| `_set_func(func)` | 写入并校验 `func` 签名 | `ConfigurationError`（参数数量 ≠ 1）、`CallableParameterKindError`（含 VAR/KEYWORD 参数） |

> 所有 setter 必须在 `start()` / `start_async()` 之前调用，**不保证**在 `start` 之后再次修改有效。

## 模板方法（子类必须实现）

`BaseTaskNode` 暴露两个**抽象钩子**供 `TaskExecutor` / `TaskSplitter` / `TaskRouter` 覆写：

| 方法 | 作用 |
|------|------|
| `get_binding_counter(downstream_name) -> ValueWrapper` | 告诉上游（predecessor）当前节点期望被绑定的下游计数器；新建的 `BaseTaskNode` 直接抛 `NotImplementedError` |
| `process_task_success(envelope, result, start_time) -> None` | 当 worker 成功拿到结果时，节点需要做"指标 + 持久化 + 下游分发"等操作；新建的 `BaseTaskNode` 直接抛 `NotImplementedError` |

> `TaskExecutor` 用 `success_counter`，`TaskSplitter` 用自己的 `split_counter`，`TaskRouter` 按下游名称维护 `route_counters`。

辅助模板方法：

- `prev_binding(pending_prev_binding)`：将前驱节点的计数器注册到当前节点的 `metrics.task_counter` 中。

## 任务注入

| 方法 | 行为 |
|------|------|
| `put_task(task)` | 把单个任务封装成 `TaskEnvelope`，并发出 `TASK_INPUT` 事件后入队；同步增加 `metrics.add_task_count` |
| `put_signal()` | 把 `TerminationSignal(source="input")` 放入队列，发出 `TERMINATION_INPUT` 事件 |
| `drain_task_queue()` | 清空剩余任务，将每条遗留任务按 `UnconsumedError()` 走 `handle_task_fail` |

> `put_task` / `put_signal` 都会同时通过 `get_lifecycle_inlet()` / `get_log_inlet()` 写持久化记录。

## 入口方法

### `run(task_source, *, if_put_signal=True)`

```python
def run(self, task_source: Iterable[T], *, if_put_signal: bool = True) -> None:
    with funnel_scope():
        for task in task_source:
            self.put_task(task)
        if if_put_signal:
            self.put_signal()
        self.start()
```

`funnel_scope()` 负责启动/关闭全局 `LifecycleSpout` / `LogSpout`。

### `async run_async(task_source, *, if_put_signal=True)`

异步版本，调用 `await self.start_async()`，同样在 `funnel_scope()` 上下文内执行。

### `restore_db(db_path, statuses=None, *, filter_by_error_type=False)`

从 sqlite 数据库加载上次未完成的任务并重放：

1. `statuses` 默认 `["failed", "pending"]`；
2. 当 `filter_by_error_type=True` 时，会按当前节点 `metrics.get_retry_error_type_names()` 过滤 `error_type`；
3. 取出 `record["task_json"]` 字段后调用 `self.run(tasks)`。

### `start()`

- 准备阶段调用 `self.metrics.reset_state()` 和 `metrics.on_start(...)`；
- 根据 `execution_mode` 选择 `dispatch.dispatch_serial()` / `dispatch.dispatch_thread()`；`async` 走 `start_async`；
- 收尾阶段 `_finish_start` 关闭 spout 计时并广播 `on_finish`；
- 任何阶段异常最终会被聚合成 `ExceptionGroup("Errors occurred during execution", ...)` 抛出。

### `async start_async()`

- 仅当 `execution_mode == "async"` 合法，否则抛 `InvalidOptionError`；
- 内部 `await self.dispatch.dispatch_async()`，异常会额外 `get_log_inlet().executor_crash(...)`。

## 结果 / 快照 / 错误处理

| 方法 | 作用 |
|------|------|
| `handle_task_fail(envelope, exception)` | 记录失败计数 + `TASK_ERROR` 事件 + 持久化失败信息 |
| `log_task_retry(envelope, exception, retry_time)` | 写入重试日志 |
| `deal_duplicate(envelope)` | 把任务标记为重复，写 `TASK_DUPLICATE` 事件 |
| `get_counts() -> dict` | 透传 `metrics.get_counts()` |
| `get_lifecycle_path() -> Path` | 返回 `LifecycleSpout.db_path` 的绝对路径（未设置时返回空 `Path`） |
| `snapshot(interval) -> dict` | 给 reporter 用的运行时快照（含 `status`、计数、估算耗时、剩余时间、平均任务耗时） |
| `get_success_pairs() -> list[tuple[T, R]]` | 从 `LifecycleSpout` 拉取成功任务与结果 |
| `get_error_pairs() -> list[tuple[T, PersistedError]]` | 拉取失败任务与 `PersistedError`（含类型与消息） |

## 关键数据流

```mermaid
flowchart LR
    subgraph "BaseTaskNode"
        PutTask[put_task] -->|envelope| TaskQueue[TaskInQueue]
        PutSignal[put_signal] -->|signal| TaskQueue
        TaskQueue --> Dispatch[TaskDispatch]
        Dispatch -->|serial / thread / async| Worker[worker / async_worker]
        Worker -->|on success| PTS[process_task_success]
        Worker -->|on fail| HTF[handle_task_fail]
        Worker -->|on retry| LTR[log_task_retry]
        Worker -->|duplicate| DD[deal_duplicate]
        PTS --> ResultQueue[TaskOutQueue]
        ResultQueue --> Downstream[(下游节点)]
        PTS --> Metrics[TaskMetrics]
        HTF --> Metrics
        DD --> Metrics
    end

    PutTask --> CT[ctree_client]
    HTF --> CT
    DD --> CT
    PTS --> CT

    PutTask --> LCI[get_lifecycle_inlet]
    PutTask --> GLI[get_log_inlet]
    PTS --> LCI
    PTS --> GLI
    HTF --> LCI
    HTF --> GLI
    DD --> LCI
    DD --> GLI
    LCI --> SQLite[(sqlite 持久化)]
    GLI --> LogStore[(日志 spout)]
```

## 使用示例

> `BaseTaskNode` 不直接对外使用，下面的示例展示如何继承它编写自定义节点；实际生产中更推荐继承 `TaskExecutor`。

```python
from celestialflow.node.core_node import BaseTaskNode
from celestialflow.runtime import TaskEnvelope


class SquareNode(BaseTaskNode[int, int]):
    """把整数平方的最小节点示例。"""

    def get_binding_counter(self, _downstream_name):
        return self.metrics.success_counter

    def process_task_success(self, envelope, result, start_time):
        # 上报 + 落库 + 转发
        task = envelope.get_task()
        result_id = self.ctree_client.emit("task.success", parents=[envelope.get_id()])
        self.metrics.add_success_count()
        for target in self.result_queue.get_target_names():
            downstream_id = self.ctree_client.emit("task.input", parents=[result_id])
            self.result_queue.put_target(TaskEnvelope(result, downstream_id), target)


node = SquareNode("Square", func=lambda x: x * x, execution_mode="serial")
node.run([1, 2, 3, 4])
print(node.get_counts())
```

## 异常一览

| 异常 | 触发场景 |
|------|---------|
| `ConfigurationError` | `_set_func` 中参数数量 ≠ 1；`set_execution_mode("async")` 但 `func` 非协程 |
| `InvalidOptionError` | `execution_mode` 不在 `("serial", "thread", "async")` |
| `CallableParameterKindError` | 回调存在非 `POSITIONAL_ONLY` / `POSITIONAL_OR_KEYWORD` 参数 |
| `NotImplementedError` | 子类未覆写 `get_binding_counter` / `process_task_success` |
| `ExceptionGroup` | `start` / `start_async` 过程中任何异常最终聚合抛出 |

## 注意事项

1. **一次性 `start`**：`start()` / `start_async()` 为一次性调用，**不保证**运行完毕后实例可被安全重置复用；如需重复执行请新建节点。
2. **setter 调用时机**：所有 setter 必须在 `start` 前完成，运行期间不要替换 `func`。
3. **生命周期托管**：全局 `LifecycleSpout` / `LogSpout` 由 `funnel_scope()` 负责启停，`BaseTaskNode` 不直接持有 spout / inlet。
4. **ctree 客户端**：默认 `LocalEventClient()` 在内部自增事件 ID，可随时通过 `set_ctree(...)` 替换为接入 `celestialtree` 的客户端。
5. **重复检查**：当 `enable_duplicate_check=True` 时，调度器在消费信封前会先调用 `metrics.is_duplicate(task_hash)`，命中后由 `deal_duplicate` 处理。
