# bench_hash_container.py 基准测试说明

> 📅 最后更新日期: 2026/05/13

## 目标

在确定使用 `bytes` 作为哈希类型后，对比不同容器结构存储 20 字节 SHA1 hash 的内存开销与查询性能，为 `processed_set` 的容器选型（纯 set vs. 支持淘汰的 LRU）提供数据支撑。

## 测试容器

| 容器 | 说明 | 适用场景 |
|------|------|---------|
| `set[bytes]` | 基准，最紧凑 | 无淘汰需求，任务量可控 |
| `dict[bytes, None]` | dict 最小开销 | 需要 dict 接口但不存值 |
| `dict[bytes, float]` | 存储时间戳 | 按时间淘汰过期条目 |
| `OrderedDict[bytes, None]` | 保序 dict | LRU 基础结构 |
| LRU(unlimited) | OrderedDict + `move_to_end` | LRU 语义，无容量限制 |
| LRU(50k) | 同上，容量上限 50,000 | 内存受限场景，淘汰最久未用 |

## 测量维度

- **容器总内存增量**：`tracemalloc` 快照差值
- **每条目平均开销**：总增量 / 条目数
- **构建耗时**：N 次插入（含 LRU 的 `move_to_end` / `popitem` 开销）
- **查询延迟**：命中 / 未命中各 0.3s 稳态测量

## 基准结果（实测）

> 环境：Windows 11，Python 3.14，N=100,000

| 容器 | 条目数 | 总内存(MB) | 每条(B) | 构建(ms) | Hit(ns) | Miss(ns) |
|------|--------|-----------|---------|---------|---------|----------|
| `set[bytes]` | 100,000 | 4.00 | 42.0 | 8.52 | 112.7 | 112.0 |
| `dict[B,None]` | 100,000 | 5.00 | 52.4 | 8.87 | 113.9 | 112.7 |
| `dict[B,float]` | 100,000 | 7.29 | 76.4 | 65.29 | 113.8 | 111.9 |
| `OrderedDict` | 100,000 | 10.05 | 105.4 | 42.08 | 122.5 | 119.4 |
| LRU(unlimited) | 100,000 | 10.05 | 105.4 | 57.25 | 115.6 | 115.1 |
| LRU(50k) | 50,000 | 8.53 | 178.8 | 69.95 | 124.0 | 115.3 |

### 内存对比（相对 set[bytes]）

| 容器 | 倍率 | 绝对值 |
|------|------|--------|
| `dict[B,None]` | 125% | 5.00 MB |
| `dict[B,float]` | 182% | 7.29 MB |
| `OrderedDict` | 251% | 10.05 MB |
| LRU(unlimited) | 251% | 10.05 MB |
| LRU(50k) | 213% | 8.53 MB |

**关键结论**：
- `set[bytes]` 最紧凑（42 B/条），但无法淘汰旧条目，长期运行内存线性增长
- `dict[B,None]` 仅多 25% 内存，若只需批量清理（如按批次 `clear()`）是最佳选择
- `OrderedDict` / LRU 内存是 set 的 2.5 倍（双向链表开销），但提供 O(1) 淘汰能力
- LRU(50k) 内存封顶在 ~8.5 MB，不管任务量多大；代价是窗口外的重复任务会漏检
- 所有容器查询性能接近（112-124 ns），容器选择对吞吐无影响
- **推荐**：默认用 `set[bytes]`；若需内存封顶，用 `OrderedDict` 实现 LRU，`maxsize` 按业务容忍度设定

## 运行方式

```bash
python bench/bench_hash_container.py
```

## 参数调整

### 修改测试规模

在 `bench/bench_hash_container.py` 的顶部修改 `N` 值：

```python
N = 10_000          # 小规模快速验证
# N = 1_000_000     # 大规模测试，观察内存线性增长
```

### 只测试特定容器

在 `main()` 中可选择性运行某些容器：

```python
def main():
    containers = [
        ("set[bytes]", benchmark_set_bytes),
        ("dict[B,None]", benchmark_dict_none),
        # ("dict[B,float]", benchmark_dict_float),      # 跳过时间戳场景
        # ("OrderedDict", benchmark_ordered_dict),
        ("LRU(unlimited)", benchmark_lru_unlimited),
        ("LRU(50k)", benchmark_lru_50k),
    ]
```

### 调整 LRU 容量

```python
# 修改 LRU(50k) 的容量上限
lru_50k_size = 10_000   # 限制在 1 万条
# lru_50k_size = 200_000  # 扩大到 20 万条
```

修改后运行：

```bash
python bench/bench_hash_container.py
```

## 依赖

- 仅标准库（`random`、`tracemalloc`、`collections`、`time`）
