# bench_hash_container.py Benchmark Documentation

> 📅 Last Updated: 2026/05/13

## Objective

After deciding to use `bytes` as the hash type, compare memory overhead and query performance of different container structures storing 20-byte SHA1 hashes, providing data to support container selection for `processed_set` (plain set vs. LRU with eviction).

## Test Containers

| Container | Description | Use Case |
|-----------|-------------|----------|
| `set[bytes]` | Baseline, most compact | No eviction needed, controllable task volume |
| `dict[bytes, None]` | Minimal dict overhead | Need dict interface but no values |
| `dict[bytes, float]` | Store timestamps | Time-based eviction of expired entries |
| `OrderedDict[bytes, None]` | Ordered dict | LRU base structure |
| LRU(unlimited) | OrderedDict + `move_to_end` | LRU semantics, no capacity limit |
| LRU(50k) | Same as above, capacity limit 50,000 | Memory-constrained scenarios, evict least recently used |

## Measurement Dimensions

- **Container total memory increment**: `tracemalloc` snapshot difference
- **Per-entry average overhead**: Total increment / number of entries
- **Build time**: N insertions (including LRU `move_to_end` / `popitem` overhead)
- **Query latency**: Hit / miss each measured over 0.3s steady state

## Benchmark Results (Measured)

> Environment: Windows 11, Python 3.14, N=100,000

| Container | Entries | Total Memory(MB) | Per Entry(B) | Build(ms) | Hit(ns) | Miss(ns) |
|-----------|---------|------------------|--------------|-----------|---------|----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 8.52 | 112.7 | 112.0 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 8.87 | 113.9 | 112.7 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 65.29 | 113.8 | 111.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 42.08 | 122.5 | 119.4 |
| LRU(unlimited) | 100,000 | 10.05 | 105.4 | 57.25 | 115.6 | 115.1 |
| LRU(50k) | 50,000 | 8.53 | 178.8 | 69.95 | 124.0 | 115.3 |

### Memory Comparison (Relative to set[bytes])

| Container | Ratio | Absolute |
|-----------|-------|----------|
| `dict[B,None]` | 125% | 5.00 MB |
| `dict[B,float]` | 182% | 7.29 MB |
| `OrderedDict` | 251% | 10.05 MB |
| LRU(unlimited) | 251% | 10.05 MB |
| LRU(50k) | 213% | 8.53 MB |

**Key Conclusions**:
- `set[bytes]` is the most compact (42 B/entry), but cannot evict old entries; memory grows linearly in long-running scenarios
- `dict[B,None]` costs only 25% more memory; if only batch cleanup is needed (e.g., `clear()` by batch), it is the best choice
- `OrderedDict` / LRU memory is 2.5x that of set (doubly-linked list overhead), but provides O(1) eviction capability
- LRU(50k) memory is capped at ~8.5 MB regardless of task volume; the trade-off is that duplicate tasks outside the window will be missed
- All containers have similar query performance (112-124 ns); container choice has no impact on throughput
- **Recommendation**: Default to `set[bytes]`; if memory capping is needed, use `OrderedDict`-based LRU with `maxsize` set according to business tolerance

## How to Run

```bash
python bench/bench_hash_container.py
```

## Dependencies

- Standard library only (`random`, `tracemalloc`, `collections`, `time`)
