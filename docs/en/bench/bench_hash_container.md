# bench_hash_container.py Benchmark Notes

> 📅 Last Updated: 2026/05/13

## Objective

After deciding to use `bytes` as the hash type, compare the memory overhead and lookup performance of different container structures that store 20-byte SHA1 hashes. The goal is to choose the right container for `processed_set`, balancing a plain set against LRU-style eviction support.

## Test Containers

| Container | Description | Suitable Scenario |
|-----------|-------------|-------------------|
| `set[bytes]` | Baseline, most compact | No eviction needed, manageable task volume |
| `dict[bytes, None]` | Minimal dict overhead | Need a dict API but no value payload |
| `dict[bytes, float]` | Stores timestamps | Evict expired entries by time |
| `OrderedDict[bytes, None]` | Ordered dictionary | Base structure for LRU |
| LRU(unlimited) | OrderedDict + `move_to_end` | LRU semantics without a size cap |
| LRU(50k) | Same as above, capped at 50,000 entries | Memory-constrained workloads with eviction |

## Measurement Dimensions

- **Total container memory increase**: measured from `tracemalloc` snapshots.
- **Average cost per entry**: total increase divided by number of entries.
- **Build time**: time for `N` insertions, including `move_to_end` and `popitem` in LRU cases.
- **Lookup latency**: steady-state hit and miss measurement over `0.3s` each.

## Benchmark Results (Measured)

> Environment: Windows 11, Python 3.14, `N=100,000`

| Container | Entries | Total Memory (MB) | Per Entry (B) | Build (ms) | Hit (ns) | Miss (ns) |
|-----------|---------|-------------------|---------------|------------|----------|-----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 8.52 | 112.7 | 112.0 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 8.87 | 113.9 | 112.7 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 65.29 | 113.8 | 111.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 42.08 | 122.5 | 119.4 |
| LRU(unlimited) | 100,000 | 10.05 | 105.4 | 57.25 | 115.6 | 115.1 |
| LRU(50k) | 50,000 | 8.53 | 178.8 | 69.95 | 124.0 | 115.3 |

### Memory Comparison (Relative to `set[bytes]`)

| Container | Ratio | Absolute Value |
|-----------|-------|----------------|
| `dict[B,None]` | 125% | 5.00 MB |
| `dict[B,float]` | 182% | 7.29 MB |
| `OrderedDict` | 251% | 10.05 MB |
| LRU(unlimited) | 251% | 10.05 MB |
| LRU(50k) | 213% | 8.53 MB |

**Key takeaways**:
- `set[bytes]` is the most compact option at `42 B` per entry, but it cannot evict old entries, so memory grows linearly over time.
- `dict[B,None]` uses only about 25% more memory and is the best option when batch cleanup such as `clear()` is enough.
- `OrderedDict` and LRU use about 2.5x the memory of a set because of doubly linked list overhead, but they provide O(1) eviction.
- LRU(50k) caps memory at about `8.5 MB` regardless of total task volume, at the cost of missing duplicates that fall outside the retained window.
- Lookup speed is nearly identical across containers (`112-124 ns`), so throughput is not the deciding factor.
- **Recommendation**: use `set[bytes]` by default; if memory must be capped, implement LRU with `OrderedDict` and tune `maxsize` based on business tolerance.

## How to Run

```bash
python bench/bench_hash_container.py
```

## Parameter Tuning

### Change the Test Scale

Modify the top-level `N` in `bench/bench_hash_container.py`:

```python
N = 10_000          # Small-scale quick verification
# N = 1_000_000     # Large-scale test to observe linear memory growth
```

### Test Only Specific Containers

Choose container cases in `main()`:

```python
def main():
    containers = [
        ("set[bytes]", benchmark_set_bytes),
        ("dict[B,None]", benchmark_dict_none),
        # ("dict[B,float]", benchmark_dict_float),      # Skip timestamp-based scenario
        # ("OrderedDict", benchmark_ordered_dict),
        ("LRU(unlimited)", benchmark_lru_unlimited),
        ("LRU(50k)", benchmark_lru_50k),
    ]
```

### Adjust the LRU Capacity

```python
# Change the capacity of LRU(50k)
lru_50k_size = 10_000   # Limit to 10k entries
# lru_50k_size = 200_000  # Expand to 200k entries
```

Run again after modification:

```bash
python bench/bench_hash_container.py
```

## Dependencies

- Standard library only (`random`, `tracemalloc`, `collections`, `time`)
