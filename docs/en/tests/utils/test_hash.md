# Hash Utility Tests (test_hash.py)

> 📅 Last Updated: 2026/05/28

## Purpose

Validates the two hash utility functions in `celestialflow.runtime.util_hash`: `make_hashable` and `object_to_hash`, ensuring that any Python object can be stably converted into a hashable form and produce a unique digest.

## Core Test Targets

- `make_hashable`: Recursively converts unhashable objects such as lists, dicts, and sets into hashable structures (tuples).
- `object_to_hash`: Computes a 20-byte SHA1 digest for any object, used for task deduplication.

## Key Test Scenarios

### `make_hashable`
- **Primitive types returned as-is**: `int`, `str`, `float`, `bool`, `None` are unchanged
- **Tuples returned as-is**: already hashable, no conversion needed
- **Empty containers**: `[]` → `()`, `{}` → `()`
- **List to tuple**: `[1, 2, 3]` → `(1, 2, 3)`
- **Nested lists**: `[[1, 2], [3, 4]]` → `((1, 2), (3, 4))`
- **Dicts**: Converted to sorted `(key, value)` tuple pairs for determinism
- **Nested dicts**: Inner values recursively converted
- **Mixed types**: Lists containing dicts and primitives
- **Sets**: Converted to sorted tuples
- **Result is hashable**: Result can be used as `set` element / `dict` key

### `object_to_hash`
- **Return type**: 20-byte `bytes`
- **Idempotency**: Same object called multiple times produces the same hash
- **Same structure = same hash**: Structurally identical objects produce the same hash
- **Different values = different hashes**: `1`, `"1"`, `[1]`, `{"a": 1}` are all distinct
- **Nested structures**: Complex nested objects are correctly computed
- **Empty container differentiation**: `[]`, `{}`, `()` produce three different hashes

## How to Run

```bash
# Run all
pytest tests/utils/test_hash.py -v

# make_hashable tests only
pytest tests/utils/test_hash.py -k "make_hashable" -v

# object_to_hash tests only
pytest tests/utils/test_hash.py -k "object_to_hash" -v

# Nested structure tests only
pytest tests/utils/test_hash.py -k "nested" -v
```

## Performance Reference

| Test Class | Duration |
|------------|----------|
| `TestUtilHash` | ~0.05s |

## Key Details

- `make_hashable` sorts dict keys and set elements before conversion, ensuring that `{"b": 2, "a": 1}` and `{"a": 1, "b": 2}` produce the same result.
- `object_to_hash` internally calls `make_hashable`, then serializes via `pickle` and computes SHA1.
- Both hashing mechanisms are used in the framework's deduplication: `make_hashable` for fast in-memory comparison, and `object_to_hash` for persistent / cross-process comparison.

## Notes

- The hash utilities are the foundation of the task deduplication feature; incorrect implementation would lead to missed duplicates or false positives.
- Related implementation is in `src/celestialflow/runtime/util_hash.py`.
