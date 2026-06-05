# bench_hash_memory.py Benchmark Notes

> 📅 Last Updated: 2026/05/13

## Objective

Compare the memory footprint and lookup performance of storing SHA1 hashes in a `set` as `str` (40-char hex), `bytes` (20 raw bytes), and `int` (160-bit integer), providing evidence for the `processed_set` data type choice.

## Test Strategy

| Type | Construction | Single-Object Size | Notes |
|------|--------------|--------------------|-------|
| `str` | `randbytes(20).hex()` | 81 B | Original approach, 40-character hex string |
| `bytes` | `randbytes(20)` | 53 B | Current approach, direct output of `hashlib.sha1().digest()` |
| `int` | `int.from_bytes(randbytes(20), 'big')` | 48 B | Most compact, but loses fixed-length semantics |

## Measurement Dimensions

- **Single-object size**: Python object memory from `sys.getsizeof()`.
- **Total set memory increase**: construct `N` objects into a set with `tracemalloc` snapshots.
- **Average cost per entry**: total increase divided by `N`, including set buckets and pointer overhead.
- **Build time**: total time for `N` calls to `set.add()`.
- **Lookup latency**: steady-state hit and miss measurements over `0.3s`, reported in nanoseconds per lookup.

## Benchmark Results (Measured)

> Environment: Windows 11, Python 3.14, `N=100,000`

| Type | Single Object (B) | Total Memory (MB) | Per Entry (B) | Build (ms) | Hit (ns) | Miss (ns) |
|------|-------------------|-------------------|---------------|------------|----------|-----------|
| `str` | 81 | 11.73 | 123.0 | 60.40 | 110.5 | 112.2 |
| `bytes` | 53 | 9.06 | 95.0 | 56.23 | 112.7 | 112.7 |
| `int` | 48 | 8.58 | 90.0 | 69.05 | 121.9 | 112.4 |

### Memory Savings (Relative to `str`)

| Type | Total Memory | Per-Entry Cost |
|------|--------------|----------------|
| `bytes` | 77.2% | 77.2% |
| `int` | 73.2% | 73.2% |

**Key takeaways**:
- Moving from `str` to `bytes` saves about 23% memory, roughly 27 MB at the million-task scale.
- Moving from `bytes` to `int` saves only about another 5%, but `int` loses fixed-length semantics and is harder to inspect during debugging.
- Lookup speed is effectively the same across all three (~112 ns), so changing type does not materially affect deduplication throughput.
- **Recommendation**: use `bytes`, because `hashlib.sha1().digest()` returns it directly with zero conversion overhead.

## How to Run

```bash
python bench/bench_hash_memory.py
```

## Parameter Tuning

### Change the Test Scale

Modify `N` near the top of `bench/bench_hash_memory.py`:

```python
N = 10_000          # Small-scale quick verification
# N = 1_000_000     # Large-scale test to observe million-entry memory differences
```

### Test Only Specific Types

Choose which cases to run in `main()`:

```python
def main():
    # benchmark_str()    # Skip the str case
    benchmark_bytes()    # Only test bytes
    # benchmark_int()    # Skip the int case
```

### Customize the Random Seed

```python
random.seed(123)  # Change the seed to produce a different hash distribution
```

Run again after modification:

```bash
python bench/bench_hash_memory.py
```

## Dependencies

- Standard library only (`random`, `sys`, `tracemalloc`, `time`)
