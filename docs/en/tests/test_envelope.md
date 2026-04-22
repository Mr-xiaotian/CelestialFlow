# test_envelope.py Test Documentation

## Test Purpose

Validates the core behavior of `TaskEnvelope`, including data wrapping/unwrapping, attribute persistence, hash consistency, and memory optimization mechanisms. `TaskEnvelope` is the fundamental unit for passing tasks between queues in CelestialFlow, and its correctness directly affects the reliability of the entire data flow.

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestTaskEnvelope` | 6 | wrap/unwrap, source, change_id, hash, slots |

### Detailed Test Case Descriptions

#### `test_wrap_unwrap`
- **Purpose**: Verifies that `TaskEnvelope.wrap()` correctly wraps arbitrary Python objects and `unwrap()` fully restores them.
- **Input**: `{"key": "value", "num": 42}`, `task_id=100`
- **Assertions**: The unwrapped task, hash, and id all match the original values; hash is a non-empty string.

#### `test_wrap_preserves_source`
- **Purpose**: Verifies that the `source` attribute is not lost during wrapping.
- **Background**: `source` is used to trace task origin (e.g., `"input"`, upstream stage's tag).

#### `test_change_id`
- **Purpose**: Verifies that `change_id()` can modify the envelope ID (used to generate new tracking IDs in retry scenarios).
- **Note**: The old ID is not preserved after modification; the caller must maintain parent-child relationships independently.

#### `test_different_tasks_different_hash`
- **Purpose**: Verifies that different payloads produce different `hash` values.
- **Mechanism**: Uses `object_to_str_hash` internally, computing based on the canonical string representation of the object.

#### `test_same_task_same_hash`
- **Purpose**: Verifies that identical payloads produce identical `hash` values.
- **Use case**: Deduplication checks (`enable_duplicate_check=True`) rely on this property.

#### `test_slots_memory_efficient`
- **Purpose**: Verifies that `__slots__` is in effect, preventing dynamic attribute addition.
- **Benefit**: Each `TaskEnvelope` instance saves approximately 50% memory (no `__dict__`).

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | Object under test |

## Potential Issues and Notes

### 1. Hash Collisions
`object_to_str_hash` computes based on string representation. The following cases may produce unexpectedly identical hashes:
- `1` and `"1"` (numeric vs. string)
- Objects of different classes with identical `__repr__` output

**Recommendation**: When using `enable_duplicate_check` in production, ensure type consistency of input tasks.

### 2. Wrapping Non-serializable Objects
`TaskEnvelope.wrap()` internally calls `object_to_str_hash`. If the task contains non-serializable objects (such as file handles or lambdas), it may fail at the hash computation stage.

**Troubleshooting**:
```python
from celestialflow.runtime.util_hash import object_to_str_hash
try:
    object_to_str_hash(your_task)
except Exception as e:
    print(f"Cannot compute hash: {e}")
```

### 3. `change_id` Has No Validation
`change_id(new_id)` does not check ID uniqueness or maintain a historical ID chain. Misuse in retry logic may cause the trace tree to break.

### 4. `__slots__` and Inheritance Limitations
If subclasses of `TaskEnvelope` are needed in the future, they must also declare `__slots__`; otherwise, the memory optimization benefits will be lost.

## How to Run

```bash
pytest tests/test_envelope.py -v
```

## Related Files

- `src/celestialflow/runtime/core_envelope.py`: Implementation under test
- `src/celestialflow/runtime/util_hash.py`: Hash computation logic
- `tests/test_queue.py`: Queue operation tests using `TaskEnvelope`
- `tests/test_metrics.py`: Deduplication tests via hash
