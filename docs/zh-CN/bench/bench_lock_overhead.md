# bench_lock_overhead.py 基准测试说明

> 📅 最后更新日期: 2026/06/16

## 目标

对比两类常见同步场景在有锁和无锁下的时间开销：

- 共享 `int` 自增
- `multiprocessing.Queue` 读写

每类场景都分别测试：

- 串行
- 并行
- 有锁
- 无锁

用于快速判断“额外加一层显式锁”在当前机器上的成本，以及并发访问时锁竞争会把开销放大到什么程度。

## 测试内容

| 测试项 | 模式 | 锁策略 | 说明 |
|--------|------|--------|------|
| `shared int` | `serial` | `no_lock` | 单进程直接对共享整数自增 |
| `shared int` | `serial` | `lock` | 单进程每次自增都进入 `Value` 的锁 |
| `shared int` | `parallel` | `no_lock` | 4 个进程并发自增 `Value(lock=False)` |
| `shared int` | `parallel` | `lock` | 4 个进程并发自增 `Value(lock=True)` |
| `MPQueue` | `serial` | `no_lock` | 单进程顺序 `put` / `get` |
| `MPQueue` | `serial` | `lock` | 单进程对每次 `put` / `get` 额外包一层显式锁 |
| `MPQueue` | `parallel` | `no_lock` | 4 个生产者 + 4 个消费者并发访问同一个队列 |
| `MPQueue` | `parallel` | `lock` | 4 个生产者 + 4 个消费者并发访问队列，并对每次操作额外包一层显式锁 |

## 关键配置

- `INT_OPS = 100_000`
- `MPQUEUE_ITEMS = 20_000`
- `PARALLEL_WORKERS = 4`
- `REPEAT = 2`
- 启动方式固定使用 `spawn`，与 Windows 默认行为保持一致

## 可能出现的问题

1. **并行 `int` 无锁结果不保证正确**：`Value(lock=False)` 的 `value += 1` 不是跨进程原子操作。本轮若碰巧结果正确，也不代表它在更大规模或其他机器上稳定正确。
2. **Windows 下 `spawn` 开销很大**：并行模式的总耗时里包含了子进程创建成本，尤其会放大 `MPQueue` 的绝对耗时。
3. **`MPQueue` 并行结果不等于纯粹的队列吞吐**：测试值同时包含进程调度、队列同步、pickle 序列化和回收尾声。
4. **显式锁是“额外一层锁”**：`multiprocessing.Queue` 自身已经有内部同步，这里的 `lock` 结果衡量的是“在外面再包一层显式锁”的附加成本。

## 基准结果（实测）

### 2026/06/16 - Windows 本地复测

> 环境：Windows，`spawn`，`INT_OPS=100000`，`MPQUEUE_ITEMS=20000`，`PARALLEL_WORKERS=4`，`REPEAT=2`

#### Shared Int

| 模式 | 锁策略 | 平均耗时 | 标准差 | 最终值（最后一轮） | 期望值 | 正确轮次 |
|------|--------|----------|--------|--------------------|--------|----------|
| `serial` | `no_lock` | 0.0078s | 0.0000s | 100000 | 100000 | 2/2 |
| `serial` | `lock` | 0.1044s | 0.0015s | 100000 | 100000 | 2/2 |
| `parallel` | `no_lock` | 0.1928s | 0.0096s | 100000 | 100000 | 2/2 |
| `parallel` | `lock` | 0.6163s | 0.0125s | 100000 | 100000 | 2/2 |

#### MPQueue

| 模式 | 锁策略 | put 阶段 | get 尾段 | 总耗时 | 标准差 | 正确轮次 |
|------|--------|----------|----------|--------|--------|----------|
| `serial` | `no_lock` | 0.0148s | 0.2954s | 0.3102s | 0.0011s | 2/2 |
| `serial` | `lock` | 0.0284s | 0.3657s | 0.3941s | 0.0054s | 2/2 |
| `parallel` | `no_lock` | 1.1135s | 0.1226s | 1.2361s | 0.0071s | 2/2 |
| `parallel` | `lock` | 1.0568s | 0.6139s | 1.6706s | 0.0807s | 2/2 |

**本轮结论**：

- 对共享 `int` 来说，显式加锁的成本非常明显：串行场景约慢 **13x**，并行场景约慢 **3.2x**
- 对 `MPQueue` 来说，串行场景下额外加锁会把总耗时拉高约 **27%**，并行场景下则会明显放大消费尾段，整体约慢 **35%**
- `MPQueue` 的并行总耗时远高于串行，不是因为队列本身退化，而是 `spawn`、进程调度和跨进程序列化在这个规模下已经压过了队列操作本身
- 本轮 `parallel + no_lock` 的共享 `int` 恰好 2/2 正确，但这不能当作“无锁跨进程自增是安全的”证据，只能说明当前规模下暂时没撞出错误

## 运行方式

```bash
python bench/bench_lock_overhead.py
```

## 参数调整

### 放大共享 `int` 压力

```python
INT_OPS = 500_000
```

### 放大队列压力

```python
MPQUEUE_ITEMS = 100_000
```

### 增加并发进程数

```python
PARALLEL_WORKERS = 8
```

### 增加重复轮数

```python
REPEAT = 5
```

## 依赖

- Python 标准库
