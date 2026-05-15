# test_envelope.py Test Documentation

> 📅 Last Updated: 2026/05/15

## Test Objective

Validates the core behavior of `TaskEnvelope` (task envelope), including construction, getter methods, lazy hashing, attribute persistence, hash consistency, and memory optimization mechanisms. `TaskEnvelope` is the fundamental unit for passing tasks between queues in CelestialFlow; its correctness directly impacts the reliability of the entire data flow.

## Test Scope

| Test Class | Test Count | Coverage |
|------------|-----------|----------|
| `TestTaskEnvelope` | 7 | Construction and getters, source, change_id, different hashes, same hash, lazy hash, slots |
| `TestObjectToHash` | 4 | Returns bytes type, SHA1 length, same input same hash, different input different hash |

### Detailed Test Case Descriptions

#### `test_create_and_getters`
- **Objective**: Validate that the constructor and getter methods correctly create and read envelope data.
- **Input**: `{"key": "value", "num": 42}`, `id=100`
- **Assertions**: `get_task()` returns the original data; `get_id()` returns 100; `get_hash()` returns `bytes` type with length > 0.

#### `test_source_preserved`
- **Objective**: Validate that the `source` attribute is not lost during construction.
- **Background**: `source` is used for tracing task origin (e.g., `"input"`, upstream stage's tag).

#### `test_change_id`
- **Objective**: Validate that `change_id()` can modify the envelope ID (used for generating new tracking IDs in retry scenarios).

#### `test_different_tasks_different_hash`
- **Objective**: Validate that different payloads produce different `hash` values.

#### `test_same_task_same_hash`
- **Objective**: Validate that identical payloads produce the same `hash` value.
- **Usage**: Deduplication checking (`enable_duplicate_check=True`) relies on this property.

#### `test_lazy_hash`
- **Objective**: Validate that `hash` is `None` at construction time and only computed on the first `get_hash()` call.
- **Assertions**: After construction, `envelope.hash is None`; after calling `get_hash()`, `envelope.hash is not None`.

#### `test_slots_memory_efficient`
- **Objective**: Validate that `__slots__` is effective, preventing dynamic attribute addition.

## Dependencies

| Dependency | Description |
|------------|-------------|
| `pytest` | Test framework |
| `celestialflow.runtime.core_envelope.TaskEnvelope` | Object under test |
| `celestialflow.runtime.util_hash.object_to_hash` | Hash utility function |

### `TestObjectToHash` Detailed Test Case Descriptions

#### `test_returns_bytes`
- **Objective**: Validate that `object_to_hash()` returns `bytes` type.

#### `test_returns_20_bytes`
- **Objective**: Validate that the SHA1 digest length is 20 bytes.

#### `test_same_input_same_hash`
- **Objective**: Validate that identical inputs produce the same hash value.

#### `test_different_input_different_hash`
- **Objective**: Validate that different inputs produce different hash values.

## How to Run

```bash
pytest tests/test_envelope.py -v
```

## Related Files

- `src/celestialflow/runtime/core_envelope.py`: Implementation under test
- `src/celestialflow/runtime/util_hash.py`: Hash computation logic
- `tests/test_queue.py`: Queue operation tests using `TaskEnvelope`
