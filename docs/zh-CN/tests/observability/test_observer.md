# tests/observer/test_observer.py

> 📅 最后更新日期: 2026/10/09

## 作用

验证 `celestialflow.observer` 中的 `Observer`（观测器基类）、`ObserverHub`（观测器聚合 hub）、内置 `PrintObserver` 与运行节点 / 任务图（`TaskExecutor` / `TaskGraph` / `TaskChain`）之间的回调契约：确保任务执行生命周期中的关键节点能正确触发观测器的 `on_task_*` 事件，`ObserverHub` 能聚合分发并对单观测器异常做隔离，图级观测器能收到全部节点的生命周期事件与图启动 / 结束事件。

## 核心测试对象

| 类 / 对象 | 来源 | 说明 |
|-----------|------|------|
| `Observer` | `celestialflow.observer` | 观测器基类，提供 `on_node_start` / `on_node_end` / `on_task_input` / `on_task_success` / `on_task_fail` / `on_task_skip` / `on_task_retry` / `on_termination_input` / `on_termination_merge` / `on_worker_crash` / `on_graph_start` / `on_graph_end` 等事件回调 |
| `ObserverHub` | `celestialflow.observer` | 观测器聚合器，显式实现每个 `on_*` 方法并向注册的观测器广播；拒绝循环注册 |
| `PrintObserver` | `celestialflow` | 内置观测器，构造参数为 `name`，输出 `[<name>] start` / `[<name>] finish` 日志，维护 `total` / `succeeded` / `failed` 计数 |
| `MetricsObserver` | `celestialflow.observer` | 指标观察者，测试经 `metrics_of(executor)` 读取节点指标 |
| `TaskExecutor` / `TaskGraph` / `TaskChain` | `celestialflow` | 运行宿主，负责在生命周期中向观测器触发事件 |
| 事件类型 | `celestialflow.observer` | `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent` / `WorkerCrashEvent` / `GraphStartEvent` / `GraphEndEvent` |

## 测试覆盖矩阵

| 测试类 | 用例 | 覆盖目标 |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_receives_full_lifecycle` | 观测器收到完整生命周期：1 个 `NodeStartEvent`、3 个 `TaskInputEvent`、3 个 `TaskSuccessEvent`、最后 1 个 `NodeEndEvent`；外部输入 `from_node is None` |
| `TestExecutorObserver` | `test_task_success_event_carries_payload_and_ids` | `TaskSuccessEvent` 携带任务、结果与增量的 `task_id` / `success_id` |
| `TestExecutorObserver` | `test_print_observer` | `PrintObserver("PrintObserverTest")` 输出 `[PrintObserverTest] start` / `finish`，`total=3` / `succeeded=2` / `failed=1` |
| `TestExecutorObserver` | `test_observer_with_errors` | 3 个任务中 2 成功 1 失败，成功/失败计数准确 |
| `TestExecutorObserver` | `test_observer_receives_skip_callback` | `on_task_skip` 收到跳过事件（1 个） |
| `TestExecutorObserver` | `test_no_observer_works` | 未挂载观测器时执行器正常运行，`metrics_of().succeeded == 3` |
| `TestExecutorObserver` | `test_multiple_observers` | 多个观测器同时收到相同回调 |
| `TestExecutorObserver` | `test_task_input_reports_upstream_source` | 任务图中上游下发的任务触发携带 `from_node == "up"` 的输入事件 |
| `TestExtendedObserver` | `test_observer_receives_retry_and_termination_events` | 重试与终止相关事件（`TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent`）也会分发给观测器 |
| `TestObserverHub` | `test_hub_explicitly_overrides_every_observer_method` | 防止转发漂移：hub 必须显式实现 `Observer` 协议的每个 `on_*` 方法 |
| `TestObserverHub` | `test_hub_isolates_observer_exception` | 单个观测器抛异常不会中断其余观测器的分发，错误转发到 stderr |
| `TestObserverHub` | `test_hub_handle_exception_backstops_failing_observer_handler` | 观测器 `handle_exception` 自身抛异常时，由 hub 兜底且不中断分发 |
| `TestObserverHub` | `test_hub_rejects_cyclic_registration` | hub 拒绝会形成循环引用的注册（自身 / 相互），抛 `ConfigurationError` |
| `TestGraphObserver` | `test_graph_observer_receives_all_nodes` | 图级观测器收到全部节点的 `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` |
| `TestGraphObserver` | `test_node_local_observer_runs_before_graph_observer` | 同一节点内，节点本地观测器先于图级观测器被调用 |
| `TestGraphObserver` | `test_graph_hub_is_injected_as_object` | 注入的是 hub 对象本身：run 之后再注册的图级观测器依然生效 |
| `TestGraphObserver` | `test_run_async_injects_graph_observers` | `run_async` 路径同样完成图级观测器注入 |
| `TestGraphObserver` | `test_graph_observer_receives_graph_events` | 图级观测器收到 `GraphStartEvent` / `GraphEndEvent`，启动事件携带图元信息（`nodes` / `edges` / `source_nodes` / `node_meta` / `class_name` / `is_dag`） |
| `TestGraphObserver` | `test_structure_supports_graph_observer` | 结构类（`TaskChain`）同样支持图级观测器 |
| `TestGraphObserver` | `test_graph_rejects_cycle_between_graph_and_node_hub` | 将 node hub 注册进 graph hub 后，注入会因循环引用而抛 `ConfigurationError` |

## 测试重点

- **事件顺序**：确保 `NodeStartEvent` 在前、`NodeEndEvent` 最后触发；节点本地观测器先于图级观测器。
- **载荷与 ID**：成功事件携带任务、结果与独立的 `task_id` / `success_id`（递增）。
- **原因追溯**：上游投递的任务通过 `from_node` 字段标识来源节点。
- **hub 异常隔离**：单个观测器抛异常（含 `handle_exception` 自身抛异常）不影响其余观测器，且不会中断分发。
- **循环防护**：观测器 / hub 拒绝形成循环引用的注册。

## 重要细节

- 使用 `RecordingObserver`（覆写所有 `on_*` 方法并收集事件）、`CountObserver` / `Counter` 等 Mock 类验证事件分发。
- `test_print_observer` 通过 `redirect_stdout(io.StringIO())` 捕获标准输出，断言含 `[PrintObserverTest] start` / `finish`，并读取观测器的 `total` / `succeeded` / `failed` 计数器。
- `test_hub_isolates_observer_exception` 与 `test_hub_handle_exception_backstops_failing_observer_handler` 用 `redirect_stderr` 捕获 hub 转发的错误信息。
- 多数用例使用 `execution_mode="serial"`，便于按顺序断言事件。

## 运行方式

```bash
# 全部执行
pytest tests/observer/test_observer.py -v

# 仅运行执行器观测器测试
pytest tests/observer/test_observer.py -k "Executor" -v

# 仅运行 ObserverHub 测试
pytest tests/observer/test_observer.py -k "Hub" -v

# 仅运行图观测器测试
pytest tests/observer/test_observer.py -k "Graph" -v
```

## 性能参考

| 测试 | 耗时 |
|------|------|
| `TestExecutorObserver` | < 1.0s |
| `TestExtendedObserver` | < 0.5s |
| `TestObserverHub` | < 0.5s |
| `TestGraphObserver` | < 1.0s（含图构建与运行） |

## 注意事项

- 重构后挂钩 / 生命周期已改为观察者 `on_task_*` 事件；`TaskExecutor` / `TaskGraph` / `TaskChain` 通过挂载的观测器（或 hub）在对应生命周期节点触发事件。
- 观测器模式是框架实现监控、日志和进度条的基础。
- `PrintObserver.__init__(name)` 要求传入节点名，用于给所有输出加上 `[name]` 前缀，避免多节点日志混淆。
- 测试代码位于 `tests/observer/test_observer.py`。