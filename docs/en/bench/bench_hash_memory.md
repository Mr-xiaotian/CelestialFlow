# bench_hash_memory.py Benchmark Documentation

> 📅 Last Updated: 2026/05/13

## Objective

Compare memory usage and query performance when storing SHA1 hash values as `str` (40-char hex), `bytes` (20-byte raw), or `int` (160-bit integer) in a `set`, providing data to support data type selection for `processed_set`.

## Test Strategy

| Type | Construction | Single Object Size | Description |
|------|-------------|-------------------|-------------|
| `str` | `randbytes(20).hex()` | 81 B | Original approach, 40-character hex string |
| `bytes` | `randbytes(20)` | 53 B | Current approach, direct output of `hashlib.sha1().digest()` |
| `int` | `int.from_bytes(randbytes(20), 'big')` | 48 B | Most compact, but loses fixed-length semantics |

## Measurement Dimensions

- **Single object size**: Python object memory returned by `sys.getsizeof()`
- **Set total memory increment**: `tracemalloc` snapshot difference after constructing N objects and adding to set
- **Per-entry average overhead**: Total increment / N (including set bucket, pointer overhead, etc.)
- **Build time**: Total time for N `set.add()` operations
- **Query latency**: Hit / miss each measured over 0.3s steady state, reported in nanoseconds per lookup

## Benchmark Results (Measured)

> Environment: Windows 11, Python 3.14, N=100,000

| Type | Per Object(B) | Total Memory(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|--------------|------------------|--------------|-----------|---------|----------|
| `str` | 81 | 11.73 | 123.0 | 60.40 | 110.5 | 112.2 |
| `bytes` | 53 | 9.06 | 95.0 | 56.23 | 112.7 | 112.7 |
| `int` | 48 | 8.58 | 90.0 | 69.05 | 121.9 | 112.4 |

### Memory Savings (Relative to str)

| Type | Total Memory | Per-entry Overhead |
|------|-------------|-------------------|
| `bytes` | 77.2% | 77.2% |
| `int` | 73.2% | 73.2% |

**Key Conclusions**:
- `str->bytes` saves ~23% memory; at million-scale tasks, this saves ~27 MB
- `bytes->int` saves only ~5% more, but `int` lacks fixed-length semantics and is less intuitive for debugging
- All three types show no significant difference in query performance (~112 ns); type switching does not affect deduplication efficiency
- **Recommendation: use `bytes`**: `hashlib.sha1().digest()` returns it directly with zero conversion overhead

## How to Run

```bash
python bench/bench_hash_memory.py
```

## Dependencies

- Standard library only (`random`, `sys`, `tracemalloc`, `time`)
