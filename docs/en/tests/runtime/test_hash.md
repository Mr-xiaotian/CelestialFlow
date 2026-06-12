# Hash Utility Tests (test_hash.py)

> 📅 Last Updated: 2026/06/05

## Purpose
Verifies that `make_hashable` and `object_to_hash` can stably handle common Python data structures, providing the foundational guarantee for task deduplication and `TaskEnvelope.get_hash()`.

## Coverage Points
- `make_hashable` recursively converts lists, dicts, sets, and nested structures into hashable representations.
- `object_to_hash` returns a fixed 20-byte SHA1 digest.
- Objects with identical structure should produce consistent hashes; different objects should produce different hashes.

## Key Scenarios
- Basic types, empty containers, nested lists, nested dicts, sets, and mixed structures.
- Same value, different objects return the same hash.
- Different types with superficially similar values (e.g., `1`, `"1"`, `[1]`, `{"a": 1}`) produce distinct hashes from one another.

## How to Run

```bash
pytest tests/runtime/test_hash.py -v
pytest tests/runtime/test_hash.py -k "make_hashable" -v
pytest tests/runtime/test_hash.py -k "object_to_hash" -v
```
