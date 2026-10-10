# tests/observer/test_observer.py

> 📅 Last Updated: 2026/10/09

## Purpose

Validates the callback contract between `Observer` (observer base class), `ObserverHub` (observer aggregation hub), the built-in `PrintObserver` in `celestialflow.observer`, and the running nodes / task graphs (`TaskExecutor` / `TaskGraph` / `TaskChain`): ensuring that key points in the task execution lifecycle correctly trigger the observer's `on_task_*` events, that `ObserverHub` aggregates and distributes events while isolating exceptions from individual observers, and that graph-level observers receive all nodes' lifecycle events as well as the graph start / end events.

## Core Test Objects

| Class / Object | Source | Description |
|-----------|------|------|
| `Observer` | `celestialflow.observer` | Observer base class, providing event callbacks such as `on_node_start` / `on_node_end` / `on_task_input` / `on_task_success` / `on_task_fail` / `on_task_skip` / `on_task_retry` / `on_termination_input` / `on_termination_merge` / `on_worker_crash` / `on_graph_start` / `on_graph_end` |
| `ObserverHub` | `celestialflow.observer` | Observer aggregator that explicitly implements each `on_*` method and broadcasts to registered observers; rejects cyclic registration |
| `PrintObserver` | `celestialflow` | Built-in observer, constructor argument `name`, outputs `[<name>] start` / `[<name>] finish` logs, maintains `total` / `succeeded` / `failed` counts |
| `MetricsObserver` | `celestialflow.observer` | Metrics observer; tests read node metrics via `metrics_of(executor)` |
| `TaskExecutor` / `TaskGraph` / `TaskChain` | `celestialflow` | Runtime hosts responsible for triggering events to observers during the lifecycle |
| Event types | `celestialflow.observer` | `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent` / `WorkerCrashEvent` / `GraphStartEvent` / `GraphEndEvent` |

## Test Coverage Matrix

| Test Class | Case | Coverage Target |
|--------|------|----------|
| `TestExecutorObserver` | `test_observer_receives_full_lifecycle` | Observer receives the full lifecycle: 1 `NodeStartEvent`, 3 `TaskInputEvent`, 3 `TaskSuccessEvent`, and 1 final `NodeEndEvent`; external input has `from_node is None` |
| `TestExecutorObserver` | `test_task_success_event_carries_payload_and_ids` | `TaskSuccessEvent` carries the task, the result, and incremental `task_id` / `success_id` |
| `TestExecutorObserver` | `test_print_observer` | `PrintObserver("PrintObserverTest")` outputs `[PrintObserverTest] start` / `finish`, with `total=3` / `succeeded=2` / `failed=1` |
| `TestExecutorObserver` | `test_observer_with_errors` | Of 3 tasks, 2 succeed and 1 fails; success/failure counts are accurate |
| `TestExecutorObserver` | `test_observer_receives_skip_callback` | `on_task_skip` receives the skip event (1) |
| `TestExecutorObserver` | `test_no_observer_works` | The executor runs normally without an attached observer, and `metrics_of().succeeded == 3` |
| `TestExecutorObserver` | `test_multiple_observers` | Multiple observers simultaneously receive the same callbacks |
| `TestExecutorObserver` | `test_task_input_reports_upstream_source` | Tasks dispatched by upstream nodes in the task graph trigger an input event carrying `from_node == "up"` |
| `TestExtendedObserver` | `test_observer_receives_retry_and_termination_events` | Retry- and termination-related events (`TaskRetryEvent` / `TerminationInputEvent` / `TerminationMergeEvent`) are also distributed to observers |
| `TestObserverHub` | `test_hub_explicitly_overrides_every_observer_method` | Prevents forwarding drift: the hub must explicitly implement each `on_*` method of the `Observer` protocol |
| `TestObserverHub` | `test_hub_isolates_observer_exception` | An exception thrown by a single observer does not interrupt distribution to the others; the error is forwarded to stderr |
| `TestObserverHub` | `test_hub_handle_exception_backstops_failing_observer_handler` | When an observer's `handle_exception` itself throws, the hub provides a backstop without interrupting distribution |
| `TestObserverHub` | `test_hub_rejects_cyclic_registration` | The hub rejects registrations that would form a cycle (itself / mutually), raising `ConfigurationError` |
| `TestGraphObserver` | `test_graph_observer_receives_all_nodes` | The graph-level observer receives all nodes' `NodeStartEvent` / `NodeEndEvent` / `TaskInputEvent` / `TaskSuccessEvent` |
| `TestGraphObserver` | `test_node_local_observer_runs_before_graph_observer` | Within the same node, the node-local observer is invoked before the graph-level observer |
| `TestGraphObserver` | `test_graph_hub_is_injected_as_object` | The hub object itself is injected: graph-level observers registered after `run` still take effect |
| `TestGraphObserver` | `test_run_async_injects_graph_observers` | The `run_async` path also completes graph-level observer injection |
| `TestGraphObserver` | `test_graph_observer_receives_graph_events` | The graph-level observer receives `GraphStartEvent` / `GraphEndEvent`; the start event carries graph metadata (`nodes` / `edges` / `source_nodes` / `node_meta` / `class_name` / `is_dag`) |
| `TestGraphObserver` | `test_structure_supports_graph_observer` | Structure classes (`TaskChain`) also support graph-level observers |
| `TestGraphObserver` | `test_graph_rejects_cycle_between_graph_and_node_hub` | After registering a node hub into the graph hub, injection raises `ConfigurationError` due to the cyclic reference |

## Test Focus

- **Event ordering**: Ensures `NodeStartEvent` fires first and `NodeEndEvent` fires last; node-local observers run before graph-level observers.
- **Payload and IDs**: Success events carry the task, the result, and independent incremental `task_id` / `success_id`.
- **Cause tracing**: Tasks dispatched upstream are identified by their source node via the `from_node` field.
- **Hub exception isolation**: An exception thrown by a single observer (including `handle_exception` itself throwing) does not affect the others and does not interrupt distribution.
- **Cycle protection**: Observers / hubs reject registrations that would form cyclic references.

## Important Details

- Uses mock classes such as `RecordingObserver` (overrides all `on_*` methods and collects events) and `CountObserver` / `Counter` to verify event distribution.
- `test_print_observer` captures standard output via `redirect_stdout(io.StringIO())`, asserts the output contains `[PrintObserverTest] start` / `finish`, and reads the observer's `total` / `succeeded` / `failed` counters.
- `test_hub_isolates_observer_exception` and `test_hub_handle_exception_backstops_failing_observer_handler` capture the errors forwarded by the hub via `redirect_stderr`.
- Most cases use `execution_mode="serial"` to make it convenient to assert events in sequence.

## How to Run

```bash
# Run all
pytest tests/observer/test_observer.py -v

# Run executor observer tests only
pytest tests/observer/test_observer.py -k "Executor" -v

# Run ObserverHub tests only
pytest tests/observer/test_observer.py -k "Hub" -v

# Run graph observer tests only
pytest tests/observer/test_observer.py -k "Graph" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestExecutorObserver` | < 1.0s |
| `TestExtendedObserver` | < 0.5s |
| `TestObserverHub` | < 0.5s |
| `TestGraphObserver` | < 1.0s (includes graph construction and running) |

## Notes

- After the refactor, hooks / lifecycle have changed to the observer's `on_task_*` events; `TaskExecutor` / `TaskGraph` / `TaskChain` trigger events at the corresponding lifecycle points through the attached observer (or hub).
- The observer pattern is the foundation for the framework's monitoring, logging, and progress bar features.
- `PrintObserver.__init__(name)` requires a node name to prefix all output with `[name]`, avoiding confusion between the logs of multiple nodes.
- The test code is located in `tests/observer/test_observer.py`.