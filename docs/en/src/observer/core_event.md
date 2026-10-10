# src/celestialflow/observer/core_event.py

> 📅 Last Updated: 2026/10/09

`core_event.py` defines **all event types** in the observer system. They serve as the input parameters of observer callbacks, describing the various changes of the task / node / task graph lifecycle. All events are read-only `dataclass`es with `frozen=True, slots=True`.

## Event Overview

| Event | Fields | Trigger Timing |
|------|------|----------|
| `NodeStartEvent` | `node`, `execution_mode`, `max_workers` | Node starts |
| `NodeEndEvent` | `node`, `execution_mode`, `max_workers`, `elapsed` | Node ends |
| `TaskInputEvent` | `node`, `task`, `task_repr`, `input_id`, `from_node` | A task enters the node's input queue |
| `TaskSuccessEvent` | `node`, `task`, `task_repr`, `result`, `result_repr`, `elapsed`, `task_id`, `success_id` | A task is processed successfully |
| `TaskFailEvent` | `node`, `task`, `task_repr`, `exception`, `task_id`, `error_id` | A task finally fails |
| `TaskSkipEvent` | `node`, `task`, `task_repr`, `task_id`, `skip_id` | A task is skipped |
| `TaskRetryEvent` | `node`, `task`, `task_repr`, `exception`, `task_id`, `retry_times` | A task fails but triggers a retry |
| `TerminationInputEvent` | `node`, `termination_id` | A termination signal enters the input queue |
| `TerminationMergeEvent` | `node`, `parent_ids`, `termination_id` | Multiple termination signals are merged |
| `WorkerCrashEvent` | `node`, `exception` | A worker thread / coroutine catches an unhandled exception in the fallback layer |
| `GraphStartEvent` | `graph`, `graph_mode`, `start_time`, `class_name`, `is_dag`, `nodes`, `edges`, `source_nodes`, `node_meta` | Task graph starts |
| `GraphEndEvent` | `graph`, `elapsed` | Task graph ends |

## Field Descriptions

### Common Fields

- `node`: node name, identifying the node to which the event belongs.
- `task`: the raw task data (`Any`); `task_repr` is its readable string representation.

### Event ID Fields

- `input_id`: the current input event ID.
- `task_id`: the task input event ID (corresponding to `TaskInputEvent.input_id`).
- `success_id` / `error_id` / `skip_id`: the event IDs of the success / error / skip events respectively.
- `termination_id`: the termination-signal event ID.
- `parent_ids`: the list of termination-signal event IDs participating in the merge.

### Task Source

- `from_node`: the upstream source node name; `None` indicates external direct injection. This field is the basis on which `MetricsObserver` distinguishes external injection from upstream delivery.

### Graph Metadata (`GraphStartEvent`)

- `graph`: the task graph name.
- `graph_mode`: the task graph run mode.
- `start_time`: the task graph start time.
- `class_name`: the task graph class name.
- `is_dag`: whether it is a DAG task graph.
- `nodes`: the task graph node name list.
- `edges`: the task graph edge adjacency list (`{from_name: [to_name, ...]}`).
- `source_nodes`: the source node name list.
- `node_meta`: build-time metadata of each node.

## Code Sample

```python
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TaskSuccessEvent:
    node: str
    task: Any
    task_repr: str
    result: Any
    result_repr: str
    elapsed: float
    task_id: int
    success_id: int
```

All events use `frozen=True, slots=True`, i.e. they are immutable (fields cannot be changed after construction, and are hashable) and save memory via `__slots__`.

## Usage Example

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskFailEvent,
    TaskSuccessEvent,
    WorkerCrashEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} succeeded: {event.result_repr}")

    def on_task_fail(self, event: TaskFailEvent) -> None:
        print(f"{event.node} failed: {event.exception}")

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        print(f"{event.node} worker crash: {event.exception}")


hub = ObserverHub()
hub.add_observer(MyObserver())
```

## Notes

1. **Read-only events**: events are all immutable `dataclass`es; observers should not modify the internal fields of an event.
2. **Constructed by the framework**: events are constructed by nodes / task graphs at the corresponding timing and `hub.on_*()` is called; they generally do not need to be constructed manually.
3. **Legacy "count-type callbacks" are deprecated**: event objects replace the basic-parameter callbacks such as `on_task_success(count)` in the legacy `BaseObserver`, carrying richer context.