# bench_hash.py Benchmark Documentation

> 📅 Last Updated: 2026/04/22

## Objective

Systematically compare 9 object-to-hash-string serialization+hashing strategies for selecting the optimal approach for `TaskEnvelope` deduplication and tracking ID generation. Evaluation dimensions include: speed, stability, collision rate, and support for different data types.

## Test Strategies

| Method | Serialization | Hash Algorithm | Characteristics |
|--------|--------------|----------------|-----------------|
| `pickle+md5` | `pickle.dumps` | MD5 | Supports arbitrary objects, but unstable (protocol version sensitive) |
| `pickle+sha1` | `pickle.dumps` | SHA1 | Same as above, longer digest |
| `pickle+blake2b16` | `pickle.dumps` | BLAKE2b(16B) | Faster, shorter digest |
| `json+md5` | Custom JSON | MD5 | Cross-language stable, but only supports JSON-serializable types |
| `json+sha256` | Custom JSON | SHA256 | More secure, but slower |
| `repr+md5` | `repr(normalized)` | MD5 | Good readability, but sensitive to `set`/`dict` ordering |
| `repr+sha1+uuid` | `repr(normalized)` | SHA1->UUID | Formatted as standard UUID |
| `repr+blake2b16` | `repr(normalized)` | BLAKE2b(16B) | Fast + short digest |
| `fast_mixed` | Type-branched (bytes/str/repr/pickle) | SHA1 | Shortcuts for primitive types, falls back to pickle for complex objects |

## Test Dataset

Covers 11 typical data shapes: `int`, `short_str`, `long_str_4k`, `bytes_4k`, `small_tuple`, `small_list`, `list_100_ints`, `small_dict`, `dict_100_pairs`, `nested_dict`, `set_100_ints`.

## Key Implementation

- `normalize_for_hash`: Converts `set`, `dict`, `tuple`, `list`, `bytes` to stable structures (sorted keys, type markers)
- `benchmark_one`: Uses `timeit.repeat` (7 repeats, 10,000 calls each), GC disabled, outputs mean and standard deviation

## Potential Issues

1. **pickle instability**: The same object may produce different `pickle.dumps` bytes across Python versions or runs (especially set ordering), resulting in inconsistent hashes. **Not suitable for cross-session deduplication**.
2. **`fast_mixed` type branch blind spots**: If a custom class without `__repr__` is passed, it falls back to `pickle.dumps`, inheriting pickle's instability issues.
3. **UUID format collision**: `repr+sha1+uuid` truncates SHA1 to 16 bytes before converting to UUID; while the probability is extremely low, it technically sacrifices cryptographic security.
4. **Large object memory pressure**: `long_str_4k` and `bytes_4k` may briefly consume significant memory during 10,000 repeated tests.

## Benchmark Results (Measured)

> Environment: Windows, Python 3.10, timeit repeat=7, number=10,000

### Overall Ranking (Average Across All Data Types)

| Method | Average Duration | Characteristics |
|--------|-----------------|-----------------|
| `fast_mixed` | ~2.5 us | Shortcuts for primitive types, fastest overall |
| `pickle+blake2b16` | ~3.0 us | pickle serialization + fast hash |
| `pickle+sha1` | ~3.2 us | Stable, good compatibility |
| `repr+blake2b16` | ~15 us | repr normalization + fast hash |
| `json+md5` / `json+sha256` | ~25 us | Cross-language stable, but slowest |
| `repr+sha1+uuid` | ~25 us | UUID format output, additional conversion overhead |

### Typical Data Points (unit: microseconds/call)

| Case | best | worst | Best Method |
|------|------|-------|-------------|
| int | ~1.3 | ~4.3 | pickle+sha1 / fast_mixed |
| short_str | ~1.3 | ~4.2 | repr+blake2b16 / fast_mixed |
| long_str_4k | ~4.1 | ~23.5 | pickle+sha1 / fast_mixed |
| bytes_4k | ~3.6 | ~58.4 | **fast_mixed** (native bytes support) |
| small_dict | ~1.9 | ~17.4 | pickle+blake2b16 |
| dict_100_pairs | ~7.8 | ~104.4 | pickle+sha1 / fast_mixed |
| list_100_ints | ~2.9 | ~36.0 | fast_mixed |
| set_100_ints | ~3.7 | ~43.1 | pickle+blake2b16 / fast_mixed |

**Key Conclusions**:
- `fast_mixed` has an absolute advantage on bytes and large collections (directly hashes raw bytes, avoiding serialization)
- `json+sha256` and `repr+sha1+uuid` are significantly slower than pickle-based approaches in all scenarios; use only when stability/format requirements are strict
- pickle-based methods perform excellently on small objects (1-3 us), but note pickle's cross-session stability risk

## How to Run

```bash
python bench/bench_hash.py
```

## Dependencies

- `celestialflow.format_table`
