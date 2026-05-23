# bench_futures_memory.py 基准测试说明

> 📅 最后更新日期: 2026/05/08

## 目标

纯粹对比线程池场景下，futures 列表"不清理"与"定期清理"两种策略的内存占用差异。不依赖 CelestialFlow 框架，隔离测量 futures 本身的内存开销。

## 背景

`ThreadPoolExecutor` 提交任务后返回 `Future` 对象。如果将所有 future 追加到列表中等待最终回收，列表会随任务数无限增长。定期过滤已完成的 future 可将列表大小限制在 `max_workers * 2`。

## 测试内容

### `dispatch_no_cleanup`
- 所有 future 追加到列表，不做任何清理
- 最终统一调用 `future.result()`

### `dispatch_with_cleanup`
- 每次追加后检查列表长度，达到 `max_workers * 2` 时过滤掉已完成的 future
- 最终对剩余 future 调用 `result()`

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `task_count` | 10K / 100K / 500K | 任务数量 |
| `max_workers` | 20 | 线程池大小 |
| 任务函数 | `noop(x)` | 直接返回，无计算开销 |

## 运行方式

```bash
python bench/bench_futures_memory.py
```

## 参数调整

### 修改任务规模和 Worker 数

在 `bench/bench_futures_memory.py` 的 `main()` 函数中调整：

```python
def main():
    scales = [10_000, 100_000, 500_000]  # 修改这里的任务数
    max_workers = 20  # 调整线程池大小
```

### 只测试某一规模

```python
def main():
    scales = [100_000]  # 仅测试 100K 任务
    max_workers = 20
```

### 调整 Worker 数以观察影响

```python
def main():
    scales = [100_000]
    max_workers = 4   # 减少 Worker，观察清理策略在不同并发度下的表现
    # max_workers = 50  # 高并发场景
```

修改后运行：

```bash
python bench/bench_futures_memory.py
```

## 基准结果（实测）

> 环境：Windows，Python 3.10，max_workers=20

| 任务数 | 模式 | 耗时 | 峰值内存 | 完成后内存 |
|--------|------|------|----------|-----------|
| 10,000 | no_cleanup | 0.351s | 17.94 MB | 0.20 MB |
| 10,000 | with_cleanup | 1.589s | 0.45 MB | 0.10 MB |
| 100,000 | no_cleanup | 5.507s | 177.01 MB | 0.18 MB |
| 100,000 | with_cleanup | 15.807s | 0.48 MB | 0.09 MB |
| 500,000 | no_cleanup | 30.232s | 883.51 MB | 0.16 MB |
| 500,000 | with_cleanup | 79.774s | 0.46 MB | 0.09 MB |

**关键结论**：
- 不清理时峰值内存与任务数线性增长：10K → 18 MB，100K → 177 MB，500K → 884 MB
- 定期清理后峰值内存恒定在 ~0.5 MB，与任务数无关
- 500K 任务场景下内存节省约 **1800x**
- 清理操作有额外耗时开销（列表过滤），但在实际框架中任务本身有计算开销，此开销可忽略

## 依赖

- `tracemalloc`（标准库）
- `concurrent.futures`（标准库）
