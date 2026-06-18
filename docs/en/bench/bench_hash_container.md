# bench_hash_container.py Benchmark Guide

> 📅 Last Updated: 2026/06/16

## Objective

After settling on `bytes` as the hash type, compare the memory overhead and lookup performance of different container structures storing 20-byte SHA1 hashes, providing data to support container selection for `processed_set` (pure set vs. LRU with eviction).

## Test Containers

| Container | Description | Use Case |
|------|------|---------|
| `set[bytes]` | Baseline, most compact | No eviction needed, manageable task volume |
| `dict[bytes, None]` | dict with minimal overhead | Need dict interface but no value storage |
| `dict[bytes, float]` | Store timestamps | Evict expired entries by time |
| `OrderedDict[bytes, None]` | Order-preserving dict | LRU base structure |
| LRU(unlimited) | OrderedDict + `move_to_end` | LRU semantics, no capacity limit |
| LRU(50k) | Same as above, capacity capped at 50,000 | Memory-constrained scenario, evicts least recently used |

## Measurement Dimensions

- **Total container memory delta**: `tracemalloc` snapshot difference
- **Average overhead per entry**: total delta / entry count
- **Build time**: N inserts (including LRU's `move_to_end` / `popitem` overhead)
- **Lookup latency**: hit / miss measured with 0.3s steady-state

## Benchmark Results (Measured)

### Historical Results - Windows 11 container comparison (date not recorded)

> Environment: Windows 11, Python 3.14, N=100,000

| Container | Entries | Total Mem(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|--------|-----------|---------|---------|---------|----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 8.52 | 112.7 | 112.0 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 8.87 | 113.9 | 112.7 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 65.29 | 113.8 | 111.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 42.08 | 122.5 | 119.4 |
| LRU(unlimited) | 100,000 | 10.05 | 105.4 | 57.25 | 115.6 | 115.1 |
| LRU(50k) | 50,000 | 8.53 | 178.8 | 69.95 | 124.0 | 115.3 |

#### Memory Comparison (relative to set[bytes])

| Container | Ratio | Absolute |
|------|------|--------|
| `dict[B,None]` | 125% | 5.00 MB |
| `dict[B,float]` | 182% | 7.29 MB |
| `OrderedDict` | 251% | 10.05 MB |
| LRU(unlimited) | 251% | 10.05 MB |
| LRU(50k) | 213% | 8.53 MB |

**Key Takeaways**:
- `set[bytes]` is the most compact (42 B/entry), but cannot evict old entries; memory grows linearly over long runs
- `dict[B,None]` uses only 25% more memory; if only batch cleanup is needed (e.g., `clear()` per batch), it is the best choice
- `OrderedDict` / LRU use 2.5x the memory of set (doubly-linked list overhead), but provide O(1) eviction capability
- LRU(50k) memory caps at ~8.5 MB regardless of task volume; the trade-off is that duplicate tasks outside the window may be missed
- All containers have similar lookup performance (112-124 ns); container choice has no impact on throughput
- **Recommendation**: Default to `set[bytes]`; if memory capping is needed, use `OrderedDict` to implement LRU with `maxsize` set according to business tolerance

### 2026/06/16 - Local retest

> Environment: Windows, N=100,000, SHA1 20-byte keys

| Container | Entries | Total Mem(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|------|--------|-----------|---------|---------|---------|----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 7.19 | 83.2 | 73.2 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 9.02 | 76.2 | 73.0 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 31.53 | 73.9 | 70.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 27.30 | 73.9 | 71.5 |
| `LRU(unlimited)` | 100,000 | 10.05 | 105.4 | 32.76 | 72.3 | 71.5 |
| `LRU(50k)` | 50,000 | 8.53 | 178.8 | 42.47 | 73.5 | 68.7 |

#### Memory Comparison (relative to set[bytes])

| Container | Ratio | Absolute |
|------|------|--------|
| `dict[B,None]` | 125.0% | 5.00 MB |
| `dict[B,float]` | 182.2% | 7.29 MB |
| `OrderedDict` | 251.3% | 10.05 MB |
| `LRU(unlimited)` | 251.3% | 10.05 MB |
| `LRU(50k)` | 213.1% | 8.53 MB |

**Supplementary conclusions for this round**:
- `set[bytes]` remains the most compact and fastest-to-build default option
- `dict[B,None]` uses only about 25% more memory; if more flexible mapping semantics are needed, it is still a very cost-effective trade-off
- The primary cost of LRU-style structures remains in linked list maintenance and extra node memory, not in lookup speed

## How to Run

```bash
python bench/bench_hash_container.py
```

## Parameter Tuning

### Adjusting Test Scale

Modify the `N` value at the top of `bench/bench_hash_container.py`:

```python
N = 10_000          # Small scale quick validation
# N = 1_000_000     # Large scale test, observe linear memory growth
```

### Testing Specific Containers Only

The container list is defined in the `configs` at the top of the script; select by commenting:

```python
configs = [
    ("set[bytes]", build_set, all_hashes),
    ("dict[B,None]", build_dict_none, all_hashes),
    # ("dict[B,float]", build_dict_float, all_hashes),      # Skip timestamp scenario
    # ("OrderedDict", build_ordered_dict, all_hashes),
    ("LRU(unlimited)", build_lru, all_hashes, 0),
    ("LRU(50k)", build_lru, all_hashes, 50_000),
]
```

### Adjusting LRU Capacity

```python
# Modify the maxsize parameter for LRU in configs
("LRU(10k)", build_lru, all_hashes, 10_000)    # Cap at 10K entries
# ("LRU(200k)", build_lru, all_hashes, 200_000) # Expand to 200K entries
```

Run after modification:

```bash
python bench/bench_hash_container.py
```

## Dependencies

- Stdlib only (`random`, `tracemalloc`, `collections`, `time`)
