# test_queue.py Test Documentation

## Test Purpose

Validates the core behavior of `TaskInQueue` (task input queue) and `TaskOutQueue` (task output queue), including: task envelope enqueue/dequeue, termination signal merging logic, invalid source validation, queue draining, broadcast/targeted sending, and dynamic queue management. These two classes form the pipeline layer of CelestialFlow's data flow engine, and their reliability directly determines the correctness of graph scheduling.

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestTaskInQueue` | 5 | put/get, termination signal direct exit, multi-source merging, unknown source error, drain |
| `TestTaskOutQueue` | 4 | Broadcast, targeted send, dynamic queue addition, duplicate tag validation |

### Key Test Case Details

#### `test_put_and_get_task`
- **Purpose**: Verifies that `TaskEnvelope` can be correctly enqueued and dequeued without data loss.
- **Mechanism**: Uses Python standard library `queue.Queue` (thread-safe) internally.

#### `test_input_termination_direct_exit`
- **Purpose**: When `source == "input"`, the termination signal should immediately return `TerminationIdPool` without waiting for other upstreams.
- **Design**: Simulates a termination signal directly injected from external sources (e.g., user via Web interface).

#### `test_multi_source_termination_merge`
- **Purpose**: In multi-upstream DAG scenarios, a merged `TerminationIdPool` is returned only after all upstreams have sent termination signals.
- **Design**: Queue tags are `["src_a", "src_b"]`; two termination signals are injected sequentially.
- **Assertions**: Merged `ids` contain `[10, 20]`.
- **Note**: After the first injection, `get()` blocks waiting until the second injection completes before returning. This is core to the framework's staged/eager termination semantics.

#### `test_unknown_source_termination_raises`
- **Purpose**: Termination signals from sources not in `queue_tags` should raise `ValueError`.
- **Security significance**: Prevents malicious or erroneous upstream nodes from sending forged termination signals that cause premature shutdown.

#### `test_drain_returns_remaining_tasks`
- **Purpose**: `drain()` should non-blockingly empty the queue, returning all remaining `TaskEnvelope` instances while recording but not returning termination signals.
- **Use case**: Resource cleanup phase after graph execution ends, collecting unconsumed tasks for persistence to failure logs.

#### `test_put_broadcasts_to_all`
- **Purpose**: `TaskOutQueue.put()` broadcasts the same envelope to all registered output queues.
- **Use case**: Fan-out edges in `TaskGraph`.

#### `test_put_target_single_queue`
- **Purpose**: `put_target(envelope, tag="b")` sends only to the queue with the specified tag.
- **Use case**: Route distribution by `TaskRouter`.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_queue` | `TaskInQueue`, `TaskOutQueue` |
| `celestialflow.persistence.core_log` | `LogSpout`, `LogInlet` (fixture dependency) |

## Potential Issues and Notes

### 1. Blocking Nature of `get()`
`TaskInQueue.get()` is a blocking call. In unit tests, if the termination signal logic has a bug (e.g., perpetually waiting for a termination signal from an upstream), the test will hang until pytest times out.

**Current timeout protection**: pytest function timeout is controlled by external configuration (e.g., `pytest-timeout` plugin). It is recommended to install `pytest-timeout` in CI:
```bash
pip install pytest-timeout
pytest tests/test_queue.py --timeout=10
```

### 2. Race Condition Between `drain` and `get`
`drain()` uses `queue.get_nowait()` for non-blocking emptying. If another thread/process is calling `put()` while `drain()` is executing, the following may occur:
- A few tasks remain after `drain()` completes
- Termination signals are not fully recorded

**Recommendation**: Only call `drain()` after all upstreams have confirmed shutdown and no new data is incoming (the framework guarantees this condition in `_finalize_nodes`).

### 3. `LogSpout` File Side Effects
The test fixture starts `LogSpout`, which creates `logs/task_logger(YYYY-MM-DD).log` files. Although tests use `log_level="ERROR"` to minimize writes, empty log files may still be generated.

**Cleanup recommendation**: Clean up logs in CI's `after_script`:
```bash
rm -rf logs/
```

### 4. Order Sensitivity of `queue_tags`
`TaskInQueue._merge_termination()` merges ID lists in the order of `queue_tags`. While current tests use `sorted()` for comparison, the order of termination IDs in production code may affect provenance tree display in CelestialTree.

### 5. Async Queue Not Covered
Current tests only cover synchronous queues (`queue.Queue`). `TaskInQueue` and `TaskOutQueue` also support `asyncio.Queue`, but the following paths are untested:
- `put_async()` / `get_async()`
- `put_channel_async()`

**Suggested addition**:
```python
@pytest.mark.asyncio
async def test_put_async():
    q = asyncio.Queue()
    in_queue = TaskInQueue(q, ...)
    await in_queue.put_async(envelope)
```

### 6. `TaskOutQueue` `put_target` Exception
If `tag` does not exist in `_tag_to_idx`, `put_target()` raises `KeyError` rather than a custom exception. This failure path is currently not covered in tests.

## How to Run

```bash
pytest tests/test_queue.py -v
```

All test cases execute in `< 500ms`.

## Related Files

- `src/celestialflow/runtime/core_queue.py`: Implementation under test
- `src/celestialflow/runtime/core_envelope.py`: `TaskEnvelope`
- `src/celestialflow/runtime/util_types.py`: `TerminationSignal`, `TerminationIdPool`
- `tests/test_graph.py`: Validates queue integration at the graph level
