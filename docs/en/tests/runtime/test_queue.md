# Runtime Queue Tests (test_queue.py)

> Last Updated: 2026/05/23

## Purpose
Validates the queue-management logic that moves tasks between stages, including enqueue/dequeue behavior, termination-signal merging and broadcasting, and dynamic queue expansion.

## Key Test Objects
- `TaskInQueue`: Wraps Python's standard `queue.Queue` and handles signal merging from multiple upstream nodes.
- `TaskOutQueue`: Broadcasts or routes tasks to multiple downstream nodes.

## Key Test Flow
1. **Input queue (`TaskInQueue`)**:
   - **Basic push/pop**: Verifies normal enqueue and dequeue of task envelopes.
   - **Termination merging**: Verifies that when a node has multiple upstreams, it waits for `TerminationSignal` from all of them before sending a termination instruction to the executor.
   - **Error handling**: Verifies that receiving a signal from an unknown source raises `UnknownNodeError`.
   - **Drain**: Verifies that all remaining tasks can be extracted from the queue at once.
2. **Output queue (`TaskOutQueue`)**:
   - **Broadcasting**: Verifies that one task is distributed to all registered downstream queues.
   - **Targeted sending**: Verifies that a task can be routed to a specific downstream node by name.
   - **Dynamic expansion**: Verifies that `add_queue` can add new downstream nodes at runtime and that duplicate names raise errors.

## Test Focus
- **Signal synchronization**: Ensures that in multi-upstream cases, a node does not miss data from other upstreams just because one upstream finished early.
- **Type safety**: Verifies that queue outputs are of the expected `TaskEnvelope` or `TerminationIdPool` type.
- **Fan-out behavior**: Ensures `TaskOutQueue` handles one-to-many distribution efficiently.

## How to Run

```bash
# Run all tests
pytest tests/runtime/test_queue.py -v

# Run input-queue tests only
pytest tests/runtime/test_queue.py -k "input" -v
pytest tests/runtime/test_queue.py -k "InQueue" -v

# Run output-queue tests only
pytest tests/runtime/test_queue.py -k "output" -v
pytest tests/runtime/test_queue.py -k "OutQueue" -v

# Run termination-merge tests only
pytest tests/runtime/test_queue.py -k "termination" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskQueue` | ~0.2s (all queue operations are in memory) |

## Important Details
- `TerminationIdPool` aggregates termination IDs from all sources for downstream traceability.
- `test_duplicate_queue_name_raises` validates the strictness of graph-structure definitions.

## Notes
- The queue mechanism is a core pillar of CelestialFlow's async non-blocking architecture.
- Related implementation: `src/celestialflow/runtime/core_queue.py`.

