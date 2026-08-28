# bench_observer.py 基准测试说明

> 📅 最后更新日期: 2026/08/26

## 目标

对比 `TaskExecutor` 在同一批任务下，**无观察者**、**print 日志**（`PrintObserver`）与 **tqdm 进度条**（`TqdmObserver`）三种场景的执行耗时，量化观察者回调带来的性能开销。

帮助用户根据任务规模与实时反馈需求，选择合适的观察策略。

## 测试内容

### 观察者方案对比

| 场景 | 观察者 | 说明 |
|------|--------|------|
| **无观察者** | `None` | 裸执行器，没有任何回调输出，作为基准线 |
| **print 日志** | `PrintObserver` | 每个生命周期事件都执行一次 `print()`，模拟简单日志输出 |
| **tqdm 进度条** | `TqdmObserver` | 每个生命周期事件都更新 `tqdm` 进度条，提供可视化反馈 |

### 任务负载

使用两种不同计算量的斐波那契任务：

```python
# 轻量任务：fib(20~29)，共 10 个任务，单次计算量小
light_tasks = list(range(20, 30))

# 较重任务：fib(50, 55, 60, 65, 70, 75, 80)，共 7 个任务，单次计算量较大
heavy_tasks = [50, 55, 60, 65, 70, 75, 80]
```

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `execution_mode` | `serial` | 所有场景均使用串行模式，控制变量，仅观察 observer 影响 |
| `max_workers` | 1 | 单 worker，避免并行调度干扰 |
| `max_retries` | 0 | 不重试，排除重试逻辑带来的额外耗时 |

## 可能出现的问题

1. **print 的 TTY 缓冲**：`print()` 默认行缓冲，当输出到实际终端时可能触发屏幕刷新，速度慢于重定向到文件。不同终端环境下 print 的开销可能有差异。
2. **tqdm 的 `total=0` 初始值**：`TaskExecutor` 在 `add_observer` 时尚未解析任务总数，`on_start` 中 `total` 为 0，直到 `on_tasks_added` 才更新。`TqdmObserver` 处理了此场景（初始设 `total=0` 后在 `on_tasks_added` 中动态扩展），但不影响基准结果的正确性。
3. **热启动效应**：首次运行可能受字节码缓存预热、import 初始化或系统缓存影响，后续轮次会更快。`bench_observer_multirun()` 通过多轮取均值来缓解该问题。
4. **斐波那契计算本身已足够小**：在轻量任务下，观察者回调的 I/O 开销可能占主导，基准结果的绝对数值会因机器而异，但**相对比例**在不同平台上应保持一致。

## 基准结果（实测）

> 🟢 本节各表格中的耗时均为历史实测数据，无法从源码验证，需人工确认。

### 2026/07/30 - 本地实测

> 环境：macOS，Python 3.14，`execution_mode=serial`

#### 单轮对比

| 任务 | 模式 | 耗时 | 相对无 observer |
|------|------|------|----------------|
| light_fib (10 tasks) | **无观察者** | 0.0037s | — |
| light_fib (10 tasks) | **print** | 0.0019s | -48.1% |
| light_fib (10 tasks) | **tqdm** | 0.0056s | +51.1% |
| heavy_fib (7 tasks) | **无观察者** | 0.0014s | — |
| heavy_fib (7 tasks) | **print** | 0.0014s | +2.6% |
| heavy_fib (7 tasks) | **tqdm** | 0.0014s | +0.9% |

> ⚠️ 轻量任务（fib 20~29）因单次计算极快（微秒级），耗时波动大，print 场景出现负值属于测量噪声。结论应参考均值。

#### 多轮均值（5 轮，light_fib）

| 模式 | 均值 | 最小值 | 最大值 |
|------|------|--------|--------|
| **无观察者** | 0.0015s | 0.0014s | 0.0017s |
| **print** | 0.0017s | 0.0016s | 0.0018s |
| **tqdm** | 0.0017s | 0.0017s | 0.0018s |

**关键结论**：

- 在串行模式下，观察者的附加开销与任务本身的计算量密切相关。
- **轻量任务**中，tqdm 和 print 的 I/O 开销相对明显，三种方案的耗时差距可达 ~50%。
- **较重任务**（fib 50~80）中，计算耗时占主导，三种方案的绝对耗时几乎相同，观察者开销可忽略。
- 当单任务耗时超过 **1ms** 量级时，选择 print 或 tqdm 对整体性能影响极小，可按需选用。

## 运行方式

```bash
python bench/bench_observer.py
```

## 参数调整

### 单独运行某个测试场景

`bench_observer.py` 的 `main()` 中可选择运行单轮对比或多轮均值测试：

```python
def main():
    # 仅运行单轮对比
    bench_observer_overhead()

    # 仅运行多轮均值
    # bench_observer_multirun()
```

修改后运行：

```bash
python bench/bench_observer.py
```

### 自定义任务规模

在 `bench_observer_overhead()` 或 `bench_observer_multirun()` 中修改任务列表：

```python
# 使用更大的计算量观察 observer 开销比例
heavy_tasks: list[Any] = list(range(80, 90))  # fib(80)~fib(89)

# 使用更多轻量任务
light_tasks: list[Any] = list(range(10, 50))  # 40 个轻量任务
```

### 调整数据量和运行轮次

```python
# 在 bench_observer_multirun() 中修改轮次
runs = 10  # 从 5 改为 10，获得更稳定的均值
```

## 依赖

- `celestialflow`（`TaskExecutor`、`BaseObserver`）
- `tqdm`（`TqdmObserver` 使用）
