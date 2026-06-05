# Hash Utility Tests (test_hash.py)

> Last Updated: 2026/06/05

## Purpose
Validates that `make_hashable` and `object_to_hash` can process common Python data structures stably, providing the foundation for task deduplication and `TaskEnvelope.get_hash()`.

## Coverage
- `make_hashable` recursively converts lists, dicts, sets, and nested structures into hashable representations.
- `object_to_hash` returns a fixed 20-byte SHA1 digest.
- Objects with the same structure should hash the same; different objects should hash differently.

## Key Scenarios
- Primitive values, empty containers, nested lists, nested dicts, sets, and mixed structures.
- Different objects with the same value produce the same hash.
- Different-looking-but-similar values such as `1`, `"1"`, `[1]`, and `{"a": 1}` must all hash differently.

## How to Run

```bash
pytest tests/runtime/test_hash.py -v
pytest tests/runtime/test_hash.py -k "make_hashable" -v
pytest tests/runtime/test_hash.py -k "object_to_hash" -v
```

