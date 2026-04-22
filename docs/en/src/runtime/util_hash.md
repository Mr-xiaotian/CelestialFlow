# RuntimeHash

`runtime/util_hash.py` provides task hashing and hashable conversion utilities.

## Main Functions

- `make_hashable(obj)`: Recursively converts list/dict/set into a stable hashable structure.
- `object_to_str_hash(obj)`: Pickles an arbitrary object and computes its SHA1 hash.

## Use Cases

- Task deduplication.
- Task identity generation.
