# bench/bench_hash_container.py
import random
import tracemalloc
from collections import OrderedDict
from time import perf_counter

# ========== 配置 ==========
N = 100_000
random.seed(42)

all_hashes: list[bytes] = [random.randbytes(20) for _ in range(N)]


# ========== 容器工厂 ==========
def build_set(hashes: list[bytes]) -> set[bytes]:
    s: set[bytes] = set()
    for h in hashes:
        s.add(h)
    return s


def build_dict_none(hashes: list[bytes]) -> dict[bytes, None]:
    d: dict[bytes, None] = {}
    for h in hashes:
        d[h] = None
    return d


def build_dict_float(hashes: list[bytes]) -> dict[bytes, float]:
    d: dict[bytes, float] = {}
    for i, h in enumerate(hashes):
        d[h] = float(i)
    return d


def build_ordered_dict(hashes: list[bytes]) -> OrderedDict[bytes, None]:
    d: OrderedDict[bytes, None] = OrderedDict()
    for h in hashes:
        d[h] = None
    return d


def build_lru(hashes: list[bytes], maxsize: int = 0) -> OrderedDict[bytes, None]:
    d: OrderedDict[bytes, None] = OrderedDict()
    for h in hashes:
        if h in d:
            d.move_to_end(h)
        else:
            d[h] = None
            if maxsize and len(d) > maxsize:
                d.popitem(last=False)
    return d


# ========== 内存测量 ==========
def measure(name: str, factory, *args) -> dict:
    tracemalloc.start()
    tracemalloc.reset_peak()
    snap1 = tracemalloc.take_snapshot()

    t0 = perf_counter()
    container = factory(*args)
    build_ms = (perf_counter() - t0) * 1000

    snap2 = tracemalloc.take_snapshot()
    diff = snap2.compare_to(snap1, "lineno")
    total = sum(stat.size_diff for stat in diff if stat.size_diff > 0)
    tracemalloc.stop()

    size = len(container)
    return {
        "name": name,
        "count": size,
        "mem_mb": total / 1024 / 1024,
        "per_item": total / size if size else 0,
        "build_ms": build_ms,
        "container": container,
    }


# ========== 查询性能 ==========
def bench_query(
    container, item_hit, item_miss, duration: float = 0.3
) -> tuple[float, float]:
    _ = item_hit in container
    _ = item_miss in container

    count = 0
    t0 = perf_counter()
    while perf_counter() - t0 < duration:
        _ = item_hit in container
        count += 1
    hit_ns = (perf_counter() - t0) / count * 1e9

    count = 0
    t0 = perf_counter()
    while perf_counter() - t0 < duration:
        _ = item_miss in container
        count += 1
    miss_ns = (perf_counter() - t0) / count * 1e9

    return hit_ns, miss_ns


# ========== 执行 ==========
configs = [
    ("set[bytes]", build_set, all_hashes),
    ("dict[B,None]", build_dict_none, all_hashes),
    ("dict[B,float]", build_dict_float, all_hashes),
    ("OrderedDict", build_ordered_dict, all_hashes),
    ("LRU(unlimited)", build_lru, all_hashes, 0),
    ("LRU(50k)", build_lru, all_hashes, 50_000),
]

fake_miss = b"\x00" * 20
results = []

for cfg in configs:
    name, factory, *args = cfg
    r = measure(name, factory, *args)

    sample = next(iter(r["container"]))
    hit_ns, miss_ns = bench_query(r["container"], sample, fake_miss)
    r["hit_ns"] = hit_ns
    r["miss_ns"] = miss_ns
    del r["container"]

    results.append(r)

# ========== 打印 ==========
print("=" * 105)
print(f"Bytes Hash Container Benchmark  (N={N:,}, SHA1 20-byte keys)")
print("=" * 105)
print(
    f"{'Container':<20} {'Count':>8} {'Total(MB)':>10} {'PerItem(B)':>11}"
    f" {'Build(ms)':>10} {'Hit(ns)':>10} {'Miss(ns)':>10}"
)
print("-" * 105)
for r in results:
    print(
        f"{r['name']:<20} {r['count']:>8,} {r['mem_mb']:>10.2f} {r['per_item']:>11.1f}"
        f" {r['build_ms']:>10.2f} {r['hit_ns']:>10.1f} {r['miss_ns']:>10.1f}"
    )

print()
base = results[0]["mem_mb"]
print(f"Memory relative to set[bytes] ({base:.2f} MB):")
for r in results[1:]:
    print(f"  {r['name']:<20} {r['mem_mb'] / base:.1%}  ({r['mem_mb']:.2f} MB)")
