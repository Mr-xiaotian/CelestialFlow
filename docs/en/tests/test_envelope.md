# test_envelope.py Test Documentation

> 📅 Last updated: 2026/05/08

## Test Purpose

Validates the core behavior of `TaskEnvelope`, including construction, getter methods, lazy hash, attribute persistence, hash consistency, and memory optimization mechanisms. `TaskEnvelope` is the fundamental unit for passing tasks between queues in CelestialFlow, and its correctness directly affects the reliability of the entire data flow.

## Test Scope

| Test Class | Cases | Coverage |
|------------|-------|----------|
| `TestTaskEnvelope` | 7 | Constructor and getters, source, change_id, different hash, same hash, lazy hash, slots |

### Detailed Test Case Descriptions

#### `test_create_and_getters`
- **Purpose**: Verifies the constructor and getter methods correctly create and read envelope data.
- **Input**: `{"key": "value", "num": 42}`, `id=100`
- **Assertions**: `get_task()` returns original data; `get_id()` returns 100; `get_hash()` is a non-empty string.

#### `test_source_preserved`
- **Purpose**: Verifies that the `source` attribute is not lost during construction.
- **Background**: `source` is used to trace task origin (e.g., `"input"`, upstream stage's tag).

#### `test_change_id`
- **Purpose**: Verifies that `change_id()` can modify the envelope ID (used to generate new tracking IDs in retry scenarios).

#### `test_different_tasks_different_hash`
- **Purpose**: Verifies that different payloads produce different `hash` values.

#### `test_same_task_same_hash`
- **Purpose**: Verifies that identical payloads produce identical `hash` values.
- **Use case**: Deduplication checks (`enable_duplicate_check=True`) rely on this property.

#### `test_lazy_hash`
- **Purpose**: Verifies that `hash` is `None` at construction time and only computed on the first call to `get_hash()`.
- **Assertions**: After construction `envelope.hash is None`; after calling `get_hash()`, `envelope.hash is not None`.

#### `test_slots_memory_efficient`
- **Purpose**: Verifies that `__slots__` is in effect, preventing dynamic attribute addition.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | Object under test |

## How to Run

```bash
pytest tests/test_envelope.py -v
```

## Related Files

- `src/celestialflow/runtime/core_envelope.py`: Implementation under test
- `src/celestialflow/runtime/util_hash.py`: Hash computation logic
- `tests/test_queue.py`: Queue operation tests using `TaskEnvelope`
