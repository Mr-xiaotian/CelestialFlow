# bench/bench_hash_memory.py

> 📅 Last Updated: 2026/10/30

## Objective

Compare the memory usage and lookup performance when storing SHA1 hash values in a `set` as three types — `str` (40-char hex), `bytes` (20-byte raw), and `int` (160-bit integer) — to inform the data type selection for `processed_set`.

> The script **constructs keys on the fly** with `random.seed(42)` + `random.randbytes(20)` to mimic the length and distribution of a SHA1 digest (so that `tracemalloc` can capture the allocations); it does not actually compute SHA1.

## Test Strategy

| Type | Construction Method | Single Object Size | Description |
|------|---------------------|-------------------|------|
| `str` | `random.randbytes(20).hex()` | 81 B | Original approach, 40-char hex string |
| `bytes` | `random.randbytes(20)` | 53 B | Current approach, equivalent to the output shape of `hashlib.sha1().digest()` |
| `int` | `int.from_bytes(random.randbytes(20), "big")` | 48 B | Most compact, but loses fixed-length semantics |

## Measurement Dimensions

- **Single object size**: Python object memory from `sys.getsizeof()`
- **Total set memory delta**: constructs N objects on the fly and adds them to a set under `tracemalloc`; after `compare_to(..., "lineno")`, only the parts with `size_diff > 0` are summed
- **Average overhead per entry**: total delta / N (including set buckets, pointers, etc. overhead)
- **Build time**: total time for N `set.add()` calls (constructed once separately from the memory measurement, so the two do not interfere)
- **Lookup latency**: hit samples use `list(s)[0]`, while miss samples are `"0" * 40` / `b"\x00" * 20` / `0` respectively; each runs a 0.3s steady-state loop and is then converted to ns/call

## Benchmark Results (Measured)

> 🟢 The memory/timing in the tables of this section are all historical measured data and cannot be verified from source code; manual confirmation is required.

### Historical Results - Windows 11 N=100,000 (date not recorded)

> Environment: Windows 11, Python 3.14, N=100,000

| Type | Single Obj(B) | Total Mem(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|---------------|---------------|--------------|-----------|---------|----------|
| `str` | 81 | 11.73 | 123.0 | 60.40 | 110.5 | 112.2 |
| `bytes` | 53 | 9.06 | 95.0 | 56.23 | 112.7 | 112.7 |
| `int` | 48 | 8.58 | 90.0 | 69.05 | 121.9 | 112.4 |

#### Memory Savings (relative to str)

| Type | Total Memory | Per-Entry Overhead |
|------|-------------|-------------------|
| `bytes` | 77.2% | 77.2% |
| `int` | 73.2% | 73.2% |

**Key Takeaways**:
- `str→bytes` saves approximately 23% memory; at million-task scale, this saves about 27 MB
- `bytes→int` saves only about 5% more, but `int` lacks fixed-length semantics and is less intuitive for debugging
- All three types have no significant difference in lookup performance (~112 ns); type switching does not affect deduplication efficiency
- **Recommended to use `bytes`**: direct return from `hashlib.sha1().digest()`, zero conversion overhead

### 2026/06/16 - Local retest

> Environment: Windows, N=100,000

| Type | Single Obj(B) | Total Mem(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|----------|-----------|---------|---------|---------|----------|
| `str` | 81 | 11.73 | 123.0 | 62.83 | 70.8 | 69.9 |
| `bytes` | 53 | 9.06 | 95.0 | 37.33 | 74.5 | 71.5 |
| `int` | 48 | 8.58 | 90.0 | 47.45 | 76.3 | 70.0 |

#### Memory Savings (relative to str)

| Type | Total Memory | Per-Entry Overhead |
|------|--------|---------|
| `bytes` | 77.2% | 77.2% |
| `int` | 73.2% | 73.2% |

**Supplementary conclusions for this round**:
- `bytes` remains the most balanced option: memory is significantly better than `str`, and build speed is fastest
- `int` is slightly better than `bytes` in memory but slower in build speed and offers no lookup advantage
- This round's lookup latencies overall fall in the `70-76 ns` range; the three formats have minimal differences, so dedup lookups are not the deciding factor for type selection

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
