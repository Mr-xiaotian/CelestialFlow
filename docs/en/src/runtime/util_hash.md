# RuntimeHash

> 📅 Last Updated: 2026/05/15

`runtime/util_hash.py` provides task hashing and hashable conversion utilities.

## Main Functions

- `make_hashable(obj)`: Recursively converts list/dict/set into stable hashable structures.
- `object_to_hash(obj)`: Pickles an arbitrary object and computes its SHA1, returning `bytes`.

## Use Cases

- Task deduplication.
- Task identity generation.
