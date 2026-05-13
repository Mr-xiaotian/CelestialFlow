
import random
import sys
import tracemalloc
from time import perf_counter

# ========== 配置 ==========
N = 100_000
random.seed(42)

# 现场构造器：确保 tracemalloc 能捕获对象分配
# 使用 random.randbytes(20) 模拟 SHA1 原始输出

def make_str():
    return random.randbytes(20).hex()   # 40字符 hex 字符串

def make_bytes():
    return random.randbytes(20)          # 20 bytes

def make_int():
    return int.from_bytes(random.randbytes(20), 'big')  # 160-bit int

# ========== 内存测量 ==========
def measure_total_memory(factory, n):
    """现场构造 n 个对象并加入 set，测量总内存增量（含对象+set开销）"""
    tracemalloc.start()
    tracemalloc.reset_peak()
    snap1 = tracemalloc.take_snapshot()
    s = set()
    for _ in range(n):
        s.add(factory())
    snap2 = tracemalloc.take_snapshot()
    diff = snap2.compare_to(snap1, 'lineno')
    total = sum(stat.size_diff for stat in diff if stat.size_diff > 0)
    tracemalloc.stop()
    return s, total

# ========== 查询性能测量（严格对齐结构） ==========
def bench_query(s, item_hit, item_miss, duration=0.3):
    # 预热
    _ = item_hit in s
    _ = item_miss in s
    
    # hit
    count = 0
    t0 = perf_counter()
    while perf_counter() - t0 < duration:
        _ = item_hit in s
        count += 1
    hit_ns = (perf_counter() - t0) / count * 1e9
    
    # miss
    count = 0
    t0 = perf_counter()
    while perf_counter() - t0 < duration:
        _ = item_miss in s
        count += 1
    miss_ns = (perf_counter() - t0) / count * 1e9
    
    return hit_ns, miss_ns

# ========== 执行 ==========
results = {}

for name, factory in [("str", make_str), ("bytes", make_bytes), ("int", make_int)]:
    # 内存测量（现场构造）
    _, mem_incr = measure_total_memory(factory, N)
    
    # 构建时间（现场构造，公平比较）
    t0 = perf_counter()
    s = set()
    for _ in range(N):
        s.add(factory())
    build_ms = (perf_counter() - t0) * 1000
    
    # 单对象大小
    single = sys.getsizeof(factory())
    
    # 查询性能（从已构建的 set 中取样）
    sample = list(s)[0]
    fake = {"str": "0" * 40, "bytes": b"\x00" * 20, "int": 0}[name]
    hit_ns, miss_ns = bench_query(s, sample, fake)
    
    results[name] = {
        "single": single,
        "mem_mb": mem_incr / 1024 / 1024,
        "per_item": mem_incr / N,
        "build_ms": build_ms,
        "hit_ns": hit_ns,
        "miss_ns": miss_ns,
    }

# ========== 打印表格 ==========
print("=" * 90)
print(f"SHA1 Hash Set Benchmark  (N={N:,} items, tracemalloc 现场构造)")
print("=" * 90)
print(f"{'Format':<8} {'Single(B)':>10} {'Total(MB)':>10} {'PerItem(B)':>11} {'Build(ms)':>10} {'Hit(ns)':>10} {'Miss(ns)':>10}")
print("-" * 90)
for name in ["str", "bytes", "int"]:
    r = results[name]
    print(f"{name:<8} {r['single']:>10} {r['mem_mb']:>10.2f} {r['per_item']:>11.1f} {r['build_ms']:>10.2f} {r['hit_ns']:>10.1f} {r['miss_ns']:>10.1f}")

print()
base_mem = results["str"]["mem_mb"]
base_per = results["str"]["per_item"]
print("Memory Reduction (relative to str):")
for name in ["bytes", "int"]:
    r = results[name]
    print(f"  {name:>5}: total={r['mem_mb']/base_mem:.1%}  per_item={r['per_item']/base_per:.1%}")
