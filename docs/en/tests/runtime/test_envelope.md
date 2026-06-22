# Task Envelope Tests (test_envelope.py)

> 📅 Last Updated: 2026/06/22

## Purpose
Verifies the `TaskEnvelope` class and the `object_to_hash` hashing utility in the `celestialflow.runtime.core_envelope` module, ensuring the integrity and consistency of task data, IDs, and hash values during transit.

## Core Test Objects
- `TaskEnvelope`: The core container that wraps task data.
- `object_to_hash`: A generic object hash computation utility.

## Test Coverage Matrix

| Test Class | Case Count | Coverage Goals |
|------------|------------|----------------|
| `TestTaskEnvelope` | 7 | Constructor/getters, ID mutation, hash consistency, lazy computation, unhashable fallback, `__slots__` memory restriction |
| `TestObjectToHash` | 4 | Return type (bytes), SHA1 fixed 20 bytes, same-input consistency, different-input divergence |

## Key Test Scenarios

### `TestTaskEnvelope`
1. **Basic attributes**: Verifies that constructor parameters (task, id) are accurately recoverable via getter methods.
2. **Hash consistency**:
   - Verifies that objects with identical content produce identical hashes (even with different IDs).
   - Verifies that different content produces different hashes.
3. **Lazy computation**: Verifies that the hash value is only computed on the first call to `get_hash()`, and the initial `hash` attribute is `None`.
4. **Unhashable task fallback**:
   - Verifies that when a task object cannot be pickled, `get_hash()` returns a unique fallback byte string prefixed with `__unhashable_task__:`.
   - Verifies that two distinct unhashable tasks do not reuse the same fallback value.
5. **Memory efficiency**: Verifies that `__slots__` is in effect, raising `AttributeError` when dynamically adding attributes.

### `TestObjectToHash`
- Verifies that the return value is always a 20-byte SHA1 digest.
- Verifies that objects with identical structure produce consistent hashes across calls.
- Verifies that different objects produce different hashes.

## Test Focus
- **Immutability simulation**: Although `TaskEnvelope` is not strictly immutable, `__slots__` restricts its extensibility.
- **Hash robustness**: Ensures `object_to_hash` can handle various Python data types.
- **Failure degradation strategy**: Ensures that unhashable tasks do not interrupt other task processing flows due to hash computation failures.
- **ID mutation**: Verifies that the `id` attribute is writable (`envelope.id = 999`), allowing tasks to be re-tagged during transit.

## How to Run

```bash
# Run all
pytest tests/runtime/test_envelope.py -v

# Envelope attribute tests only
pytest tests/runtime/test_envelope.py -k "Envelope" -v

# object_to_hash tests only
pytest tests/runtime/test_envelope.py -k "ObjectToHash" -v

# Hash consistency tests only
pytest tests/runtime/test_envelope.py -k "hash" -v

# Unhashable task fallback tests only
pytest tests/runtime/test_envelope.py -k "unhashable" -v

# Slots memory tests only
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskEnvelope` | ~0.1s (pure in-memory operations) |
| `TestObjectToHash` | < 0.1s (pure in-memory operations) |

## Important Details
- Hash computation excludes the `id` field, ensuring that tasks with identical content but different IDs are identified as duplicates.
- For tasks that cannot be pickled, the test verifies that a unique fallback value with a dedicated prefix is returned rather than propagating the exception upward.
- `test_slots_memory_efficient` uses `pytest.raises(AttributeError)` to verify the memory optimization constraint.

## Notes
- The task envelope is the unified format for transferring data between different nodes in the system.
- The related implementation is located at `src/celestialflow/runtime/core_envelope.py`.
