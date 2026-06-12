# Runtime Queue Tests (test_queue.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Verifies the queue management logic for task flow between different nodes (Stages), including task enqueue/dequeue, termination signal merging and broadcasting, and dynamic queue expansion.

## Core Test Objects
- `TaskInQueue`: Wraps Python's standard `queue.Queue`, responsible for merging signals from multiple upstream sources.
- `TaskOutQueue`: Responsible for broadcasting or targeted delivery of tasks to multiple downstream nodes.

## Key Test Scenarios

### `TestTaskInQueue` — Input Queue
| Case | Coverage Goal |
|------|---------------|
| `test_put_and_get_task` | Basic access: enqueue and dequeue `TaskEnvelope` |
| `test_input_termination_direct_exit` | An externally injected `TerminationSignal` should be returned directly |
| `test_multi_source_termination_merge` | Termination signals from multiple upstream sources must all arrive before a merged signal is returned |
| `test_unknown_source_termination_raises` | A termination signal from an unknown source raises `UnknownNodeError` |
| `test_drain_returns_remaining_tasks` | `drain()` empties the queue and returns all remaining tasks |

### `TestTaskOutQueue` — Output Queue
| Case | Coverage Goal |
|------|---------------|
| `test_put_broadcasts_to_all` | `put()` broadcasts to all downstream queues |
| `test_put_target_single_queue` | `put_target()` sends only to the specified queue |
| `test_add_queue` | Dynamically add an output queue |
| `test_duplicate_queue_name_raises` | Duplicate target name raises `DuplicateNodeError` |

## Test Focus
- **Signal Synchronization**: Ensures that in a multi-upstream environment, a node does not lose data from other upstream sources because one upstream ends early.
- **Type Safety**: Verifies that objects retrieved from the queue conform to the expected `TaskEnvelope` or `TerminationIdPool` type.
- **Fan-Out Logic**: Ensures `TaskOutQueue` can efficiently handle one-to-many data distribution.

## How to Run

```bash
# Run all
pytest tests/runtime/test_queue.py -v

# Input queue tests only
pytest tests/runtime/test_queue.py -k "InQueue" -v

# Output queue tests only
pytest tests/runtime/test_queue.py -k "OutQueue" -v

# Signal merging tests only
pytest tests/runtime/test_queue.py -k "termination" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskInQueue` / `TestTaskOutQueue` | ~0.2s (all queue operations are in-memory) |

## Important Details
- `TerminationIdPool` is used to aggregate termination IDs from all sources, facilitating later tracing.
- `test_duplicate_queue_name_raises` verifies the strictness of graph structure definitions.

## Notes
- The queue mechanism is a core pillar of CelestialFlow's asynchronous non-blocking architecture.
- The related implementation is located at `src/celestialflow/runtime/core_queue.py`.
