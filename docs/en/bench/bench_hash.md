# bench_hash.py Benchmark Notes

> 📅 Last Updated: 2026/04/22

## Objective

Systematically compare 9 object-to-hash-string strategies based on serialization plus hashing, in order to choose the best option for `TaskEnvelope` deduplication and tracking ID generation. The evaluation covers speed, stability, collision risk, and support for different data types.

## Test Strategies

| Method | Serialization | Hash Algorithm | Characteristics |
|--------|---------------|----------------|-----------------|
| `pickle+md5` | `pickle.dumps` | MD5 | Supports arbitrary objects, but unstable across protocol versions |
| `pickle+sha1` | `pickle.dumps` | SHA1 | Same as above, with a longer digest |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | Faster, short digest |
| `json+md5` | Custom JSON | MD5 | Stable across languages, but only supports JSON-serializable values |
| `json+sha256` | Custom JSON | SHA256 | More secure, but slower |
| `repr+md5` | `repr(normalized)` | MD5 | Readable, but sensitive to `set`/`dict` ordering |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1 -> UUID | Formatted as a standard UUID |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | Fast plus short digest |
| `fast_mixed` | Type-branching (`bytes` / `str` / `repr` / `pickle`) | SHA1 | Fast path for simple types, falls back to pickle for complex ones |

## Test Dataset

Covers 11 common data shapes: `int`, `short_str`, `long_str_4k`, `bytes_4k`, `small_tuple`, `small_list`, `list_100_ints`, `small_dict`, `dict_100_pairs`, `nested_dict`, and `set_100_ints`.

## Key Implementation

- `normalize_for_hash`: converts `set`, `dict`, `tuple`, `list`, and `bytes` into stable structures with sorted keys and type markers.
- `benchmark_one`: uses `timeit.repeat` (7 repeats, 10,000 calls each), disables GC, and reports mean plus standard deviation.

## Potential Issues

1. **Pickle instability**: for the same object, `pickle.dumps` may produce different bytes across Python versions or runs, especially for unordered containers, which makes the hash inconsistent. **Not suitable for cross-session deduplication**.
2. **Type blind spots in `fast_mixed`**: when a custom class is passed without a useful `__repr__`, the implementation falls back to `pickle.dumps`, which reintroduces pickle instability.
3. **UUID truncation trade-off**: `repr+sha1+uuid` truncates SHA1 to 16 bytes before converting it to a UUID. The collision probability is still extremely low, but it does reduce cryptographic strength in the strict sense.
4. **Memory pressure for large objects**: `long_str_4k` and `bytes_4k` can temporarily consume significant memory during the 10,000-call benchmark loop.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, `timeit repeat=7`, `number=10,000`

### Overall Ranking (Average Across All Data Types)

| Method | Average Time | Characteristics |
|--------|--------------|-----------------|
| `fast_mixed` | ~2.5 us | Fast path for primitive types, best overall |
| `pickle+blake2b16` | ~3.0 us | Pickle serialization plus fast hashing |
| `pickle+sha1` | ~3.2 us | Good compatibility and consistent performance |
| `repr+blake2b16` | ~15 us | Normalized repr plus fast hashing |
| `json+md5` / `json+sha256` | ~25 us | Stable across languages, but slowest |
| `repr+sha1+uuid` | ~25 us | UUID-formatted output with extra conversion overhead |

### Typical Data Points (Unit: Microseconds per Call)

| Case | best | worst | Best Method |
|------|------|-------|-------------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed** (native bytes path) |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**Key takeaways**:
- `fast_mixed` has a clear advantage on `bytes` and large collections because it can hash raw bytes directly and skip serialization.
- `json+sha256` and `repr+sha1+uuid` are noticeably slower than pickle-based approaches in every scenario, and only make sense when output stability or UUID formatting is a hard requirement.
- Pickle-based methods perform very well on small objects (`1-3 us`), but they still carry cross-session stability risks.

## How to Run

```bash
python bench/bench_hash.py
```

## Parameter Tuning

### Test Only Specific Hash Methods

In `bench/bench_hash.py`, methods and datasets are defined in `hash_methods` and `test_data`. You can comment out entries to focus on one subset:

```python
hash_methods = [
    # ("pickle+md5", hash_pickle_md5),
    # ("pickle+sha1", hash_pickle_sha1),
    ("json+md5", hash_json_md5),        # Only test JSON-based methods
    ("json+sha256", hash_json_sha256),  # Only test JSON-based methods
    # ("repr+md5", hash_repr_md5),
    # ...
]
```

### Test Only Specific Data Types

```python
test_data = [
    ("int", 12345),
    ("short_str", "hello"),
    ("long_str_4k", "A" * 4096),     # Only test large strings
    # ("bytes_4k", b"B" * 4096),
    # ...
]
```

### Adjust the Number of `timeit` Repeats

```python
# Reduce repeats for quick validation (less stable results)
results = benchmark_one(
    name, method, test_data,
    repeat=3,       # Default is 7
    number=1_000    # Default is 10,000
)
```

Run again after modification:

```bash
python bench/bench_hash.py
```

## Dependencies

- `celestialflow.format_table`
