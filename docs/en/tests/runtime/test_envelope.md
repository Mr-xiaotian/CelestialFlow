# tests/runtime/test_envelope.py

> 📅 Last Updated: 2026/09/24

## Purpose
Verifies the `TaskEnvelope` class in the `celestialflow.runtime.core_envelope` module, ensuring that task data and IDs are correctly stored by the envelope and restored via getters, and that the `__slots__` memory constraint is in effect.

## Core Test Objects
- `TaskEnvelope`: The core container that wraps task data and task ID, using `__slots__ = ("_id", "_task")` to restrict instance attributes.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestTaskEnvelope` | 3 | Constructor/getters, `get_id` query, `__slots__` memory restriction |

## Key Test Scenarios

### `TestTaskEnvelope`
1. **Construction and restoration** (`test_create_and_getters`): Constructs an envelope with a dict task `{"key": "value", "num": 42}` and `id=100`, verifying that `get_task()` returns the original task and `get_id()` returns 100.
2. **ID query** (`test_get_id`): Constructs with a string task `"hello"` and `id=1`, verifying that `get_id()` returns 1.
3. **Memory efficiency** (`test_slots_memory_efficient`): Verifies that the `__slots__` mechanism is in effect, raising `AttributeError` when dynamically adding `extra_attr` to an instance.

## Test Focus
- **Data integrity**: The envelope must losslessly preserve the task object and ID.
- **Non-extensibility**: `__slots__` prevents dynamic attributes, keeping memory usage under control.

## How to Run

```bash
# Run all
pytest tests/runtime/test_envelope.py -v

# Getter-related tests only
pytest tests/runtime/test_envelope.py -k "get_id or getters" -v

# slots memory tests only
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskEnvelope` | < 0.1s (pure in-memory operations) |

## Important Details
- `test_create_and_getters` uses a non-scalar (dict) task, verifying that the envelope can preserve any object type as-is.
- `test_slots_memory_efficient` uses `pytest.raises(AttributeError)` to verify the memory optimization constraint.

## Notes
- The task envelope is the unified format for transferring data between different nodes in the system.
- The related implementation is located at `src/celestialflow/runtime/core_envelope.py`.
