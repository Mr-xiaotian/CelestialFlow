# bench_hash_memory.py Benchmark Notes

> 📅 Last Updated: 2026/06/11

## Objective

Compare the memory usage and lookup performance when storing SHA1 hash values in a `set` as three types — `str` (40-char hex), `bytes` (20-byte raw), and `int` (160-bit integer) — to inform the data type selection for `processed_set`.

## Test Strategy

| Type | Construction Method | Single Object Size | Description |
|------|---------------------|-------------------|-------------|
| `str` | `randbytes(20).hex()` | 81 B | Original approach, 40-char hex string |
| `bytes` | `randbytes(20)` | 53 B | Current approach, direct output from `hashlib.sha1().digest()` |
| `int` | `int.from_bytes(randbytes(20), 'big')` | 48 B | Most compact, but loses fixed-length semantics |

## Measurement Dimensions

- **Single object size**: Python object memory from `sys.getsizeof()`
- **Total set memory delta**: `tracemalloc` snapshot difference after constructing N objects and adding to set
- **Average overhead per entry**: total delta / N (including set bucket, pointer, etc. overhead)
- **Build time**: Total time for N `set.add()` calls
- **Lookup latency**: hit / miss measured with 0.3s steady-state, reported in nanoseconds per lookup

## Benchmark Results (Measured)

> Environment: Windows 11, Python 3.14, N=100,000

| Type | Single Obj(B) | Total Mem(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|---------------|---------------|--------------|-----------|---------|----------|
| `str` | 81 | 11.73 | 123.0 | 60.40 | 110.5 | 112.2 |
| `bytes` | 53 | 9.06 | 95.0 | 56.23 | 112.7 | 112.7 |
| `int` | 48 | 8.58 | 90.0 | 69.05 | 121.9 | 112.4 |

### Memory Savings (relative to str)

| Type | Total Memory | Per-Entry Overhead |
|------|-------------|-------------------|
| `bytes` | 77.2% | 77.2% |
| `int` | 73.2% | 73.2% |

**Key Takeaways**:
- `str→bytes` saves approximately 23% memory; at million-task scale, this saves about 27 MB
- `bytes→int` saves only about 5% more, but `int` lacks fixed-length semantics and is less intuitive for debugging
- All three types have no significant difference in lookup performance (~112 ns); type switching does not affect deduplication efficiency
- **Recommended to use `bytes`**: direct return from `hashlib.sha1().digest()`, zero conversion overhead

## How to Run

```bash
python bench/bench_hash_memory.py
```

## Parameter Tuning

### Adjusting Test Scale

Modify the `N` value at the top of `bench/bench_hash_memory.py`:

```python
N = 10_000          # Small scale quick validation
# N = 1_000_000     # Large scale test (observe memory difference at million scale)
```

### Testing Specific Types Only

The type comparison loop in the script is defined in `for name, factory in [("str", make_str), ...]`; skip types by commenting:

```python
for name, factory in [
    # ("str", make_str),   # Skip str type
    ("bytes", make_bytes),  # Test bytes only
    # ("int", make_int),    # Skip int type
]:
```

### Customizing Random Seed

```python
random.seed(123)  # Change seed for different hash value distribution
```

Run after modification:

```bash
python bench/bench_hash_memory.py
```

## Dependencies

- Stdlib only (`random`, `sys`, `tracemalloc`, `time`)
