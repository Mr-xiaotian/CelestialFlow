# tests/runtime/test_queue.py

> 📅 Last Updated: 2026/11/13

## Purpose
Verifies the queue management logic for task flow between different nodes (Stages), including task enqueue/dequeue, termination signal merging and broadcasting, and dynamic queue expansion.

## Core Test Objects
- `TaskInQueue`: Wraps Python's standard `queue.Queue`, responsible for merging signals from multiple upstream sources.
- `TaskOutQueue`: Responsible for broadcasting or targeted delivery of tasks to multiple downstream nodes.

## Key Test Scenarios

### `TestTaskInQueue` — Input Queue
The `simple_queue` fixture constructs an input queue without any upstream source (only `out_name="test"`) for reuse in single-source cases.

| Case | Coverage Goal |
|------|---------------|
| `test_put_and_get_task` | Basic access: enqueue and dequeue `TaskEnvelope`, with the task and ID returned as-is |
| `test_input_termination_direct_exit` | A `TerminationSignal` whose source is `"input"` is converted directly into a `TerminationIdPool` containing only that ID |
| `test_multi_source_termination_merge` | After two upstreams each send one termination signal, `get()` returns a merged ID pool containing `{10, 20}` (compared after sorting in the assertions; in the implementation, `get()` keeps waiting until all upstreams have reported) |
| `test_unknown_source_termination_raises` | A termination signal from an unknown source raises `UnknownNodeError` (matching `"unknown queue source name"`) |
| `test_drain_returns_remaining_tasks` | `drain()` empties the queue and returns all remaining tasks in enqueue order, after which the queue is empty |

### `TestTaskOutQueue` — Output Queue
The output queue uses the standard library `queue.Queue` as the actual sink, verifying the visible result of broadcast/targeted delivery.

| Case | Coverage Goal |
|------|---------------|
| `test_put_broadcasts_to_all` | `put()` broadcasts the same envelope to all downstream queues |
| `test_put_target_single_queue` | `put_target()` sends only to the specified queue, leaving the other queues empty |
| `test_add_queue` | After dynamically adding an output queue, the new queue also receives broadcasts |
| `test_duplicate_queue_name_raises` | A duplicate target name raises `DuplicateNodeError` (matching `"duplicate queue target name"`) |

## Test Focus
- **Signal Synchronization**: Ensures that in a multi-upstream environment, a node does not lose data from other upstream sources because one upstream ends early.
- **Type Safety**: Verifies that objects retrieved from the queue conform to the expected `TaskEnvelope` or `TerminationIdPool` type.
- **Fan-Out Logic**: Ensures `TaskOutQueue` can efficiently handle one-to-many data distribution.

## How to Run

```bash
# Run all
uv run pytest tests/runtime/test_queue.py -v

# Input queue tests only
uv run pytest tests/runtime/test_queue.py::TestTaskInQueue -v

# Output queue tests only
uv run pytest tests/runtime/test_queue.py::TestTaskOutQueue -v

# Signal merging tests only
uv run pytest tests/runtime/test_queue.py -k "termination" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskInQueue` / `TestTaskOutQueue` | < 0.1s (all queue operations are in-memory) |

## Important Details
- `TerminationIdPool` is used to aggregate termination IDs from all sources, facilitating later tracing.
- `TaskInQueue.drain()` only returns `TaskEnvelope`s; termination signals encountered along the way are only recorded into `termination_dict` and the ID pool is not returned.
- Duplicate source names / duplicate target names are raised as `DuplicateNodeError` by `add_source_name` and `add_queue` respectively; this file only covers the latter.
- `test_duplicate_queue_name_raises` verifies the strictness of graph structure definitions.

## Notes
- The queue mechanism is a core pillar of CelestialFlow's asynchronous non-blocking architecture.
- The related implementation is located at `src/celestialflow/runtime/core_queue.py`.
