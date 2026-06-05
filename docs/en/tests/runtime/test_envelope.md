# Task Envelope Tests (test_envelope.py)

> Last Updated: 2026/06/05

## Purpose
Validates the `TaskEnvelope` class in `celestialflow.runtime.core_envelope`, ensuring task data, IDs, sources, and hashes remain complete and consistent while traveling through the pipeline.

## Key Test Objects
- `TaskEnvelope`: Core container that wraps task data.
- `object_to_hash`: Generic object-hash helper.

## Key Test Flow
1. **Basic properties**: Verifies that constructor arguments (`task`, `id`, `source`) can be read back correctly through getters.
2. **Hash consistency**:
   - Verifies that objects with the same content produce the same hash, while different content produces different hashes.
   - Verifies that the hash length is fixed at 20 bytes (SHA1).
3. **Lazy computation**: Verifies that the hash is computed only on the first `get_hash()` call to reduce memory and CPU cost.
4. **Fallback for unhashable tasks**:
   - Verifies that when a task object cannot be pickled, `TaskEnvelope.get_hash()` returns a fallback byte string unique to the current envelope.
   - Verifies that this fallback value is not reused by other unhashable envelopes.
5. **Memory efficiency**: Verifies that `__slots__` is enforced so invalid dynamic attributes cannot be added to envelope objects.

## Test Focus
- **Simulated immutability**: `TaskEnvelope` is not strictly immutable, but `__slots__` limits accidental extension.
- **Hash robustness**: Ensures `object_to_hash` works for common Python data types such as dicts, lists, strings, and numbers.
- **Failure degradation strategy**: Ensures unhashable tasks do not break the rest of the processing flow when hashing fails.
- **ID mutation**: Verifies that the `id` property remains writable so tasks can be relabeled in transit.

## How to Run

```bash
# Run all tests
pytest tests/runtime/test_envelope.py -v

# Run hash-consistency tests only
pytest tests/runtime/test_envelope.py -k "hash" -v

# Run lazy-computation tests only
pytest tests/runtime/test_envelope.py -k "lazy" -v

# Run unhashable fallback tests only
pytest tests/runtime/test_envelope.py -k "unhashable" -v

# Run slots memory tests only
pytest tests/runtime/test_envelope.py -k "slots" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestTaskEnvelope` | ~0.1s (in-memory only) |

## Important Details
- Hash calculation excludes the `id` field so tasks with the same content but different IDs are still recognized as duplicates.
- For tasks that cannot be pickled, the tests verify that `TaskEnvelope` returns a unique fallback value with a dedicated prefix instead of propagating the exception upward.
- `test_slots_memory_efficient` uses `pytest.raises(AttributeError)` to verify the memory constraint.

## Notes
- The task envelope is the unified data format used to pass work between nodes.
- Related implementation: `src/celestialflow/runtime/core_envelope.py`.

