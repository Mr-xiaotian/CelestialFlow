# RuntimeHash

> 📅 Last Updated: 2026/05/15

`runtime/util_hash.py` provides task hashing and hashable-conversion utilities.

## Main Functions

- `make_hashable(obj)`: Recursively converts list/dict/set into a stable hashable structure.
  - **Params**: `obj` (`Any`) — the object to convert. Supports nested `list`, `dict`, `set`, `tuple`, and other types.
  - **Returns**: A hashable Python object (typically `tuple` or a frozen structure). Lists and sets become sorted tuples; dicts become sorted `(key, value)` tuples.
- `object_to_hash(obj)`: Pickles an arbitrary object then computes its SHA1 hash, returning `bytes`.
  - **Params**: `obj` (`Any`) — the object to hash. Uses `pickle` protocol `5` for serialization.
  - **Returns**: `bytes` — a 20-byte SHA1 digest.

## Usage Examples

The following examples demonstrate usage of `make_hashable` and `object_to_hash`.

```python
from celestialflow.runtime.util_hash import make_hashable, object_to_hash

# ===== make_hashable =====
# Convert non-hashable objects to hashable stable forms

# List → ordered tuple
items = [3, 1, 2]
hashable_list = make_hashable(items)
print(f"List {items} → {hashable_list}")
print(f"Hashable: {isinstance(hashable_list, tuple)}")  # True

# Nested dict → sorted (key, value) tuples
data = {"b": 2, "a": 1, "c": [3, 2, 1]}
hashable_dict = make_hashable(data)
print(f"Dict {data} → {hashable_dict}")

# Set → sorted tuple
s = {3, 1, 2}
hashable_set = make_hashable(s)
print(f"Set {s} → {hashable_set}")

# Can be used directly as key in set or dict
seen = set()
seen.add(make_hashable({"name": "alice", "age": 30}))
print(f"{"alice".upper()} processed?: {make_hashable({"name": "alice", "age": 30}) in seen}")  # True

# ===== object_to_hash =====
# Compute SHA1 byte string for any object

hash_bytes = object_to_hash({"task": "process", "id": 42})
print(f"SHA1 bytes: {hash_bytes.hex()}")
print(f"Length: {len(hash_bytes)} bytes")  # 20 (SHA1)

# Same content produces the same hash
hash_bytes_2 = object_to_hash({"task": "process", "id": 42})
print(f"Consistency: {hash_bytes == hash_bytes_2}")  # True
```

## Use Cases

- Task dedup.
- Task identity generation.
