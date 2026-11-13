# bench/bench_observer.py

> 📅 最后更新日期: 2026/11/13

## 目标

对比 `TaskExecutor` 在同一批任务下，**无观察者**、**print 日志**（框架内置的 `PrintObserver`，构造时需传入 `name` 前缀）与 **tqdm 进度条**（`TqdmObserver`，由 `bench_observer.py` 内定义）三种场景的执行耗时，量化观察者事件回调带来的性能开销。

帮助用户根据任务规模与实时反馈需求，选择合适的观察策略。

## 测试内容

### 观察者方案对比

| 场景 | 观察者 | 说明 |
|------|--------|------|
| **无观察者** | `None` | 裸执行器，没有任何回调输出，作为基准线 |
| **print 日志** | `PrintObserver` | 在统一的 `on_event` 中按事件类型（节点起止、任务输入 / 成功 / 失败 / 跳过）打印带 `name` 前缀的统计行，模拟简单日志输出 |
| **tqdm 进度条** | `TqdmObserver` | 在统一的 `on_event` 中按同一组事件类型更新 `tqdm` 进度条，提供可视化反馈 |

### 任务负载

使用两种不同计算量的斐波那契任务：

```python
# 轻量任务：fib(20~29)，共 10 个任务
light_tasks = list(range(20, 30))

# “较重”任务：fib(50, 55, 60, 65, 70, 75, 80)，共 7 个任务
# 注意 fibonacci 是迭代 O(n) 实现，fib(80) 也只有约 80 次循环，单任务仍为微秒级
heavy_tasks = [50, 55, 60, 65, 70, 75, 80]
```

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `execution_mode` | `serial` | 所有场景均使用串行模式，控制变量，仅观察 observer 影响 |
| `max_workers` | 1 | 单 worker，避免并行调度干扰 |
| `max_retries` | 0 | 不重试，排除重试逻辑带来的额外耗时 |

## 关键函数

### `run_benchmark`

```python
def run_benchmark(
    name: str,
    task_data: list[Any],
    func: Any,
    *,
    observer: Observer | None = None,
) -> float
```

构造一个 `TaskExecutor(name, func, execution_mode="serial", max_workers=1, max_retries=0)`，
若传入 `observer` 则调用 `executor.add_observer(observer)`，随后用 `time.perf_counter()`
包住 `executor.run(task_data)` 并返回耗时（秒）。每次调用都新建执行器，避免状态残留。

### `TqdmObserver`

`TqdmObserver` 继承框架的 `Observer` 基类，只覆写统一入口 `on_event(event: Event)`，
并用 `match event` 按事件类型分派（`handle_exception` 保持基类默认实现）：

| 事件 | 行为 |
|------|------|
| `NodeStartEvent` | 用当前累计的 `_total` 创建 `tqdm(total=...)` |
| `TaskInputEvent` | `_total += 1`；进度条已创建时同步扩展 `total` 并 `refresh()` |
| `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` | 复用 `_advance(1)` 推进进度 |
| `NodeEndEvent` | 关闭进度条 |

未列出的 `TaskRetryEvent`、终止信号事件与图事件不会命中任何分支，由 `match` 自然忽略。
`Observer` 基类当前只提供 `on_event` 与 `handle_exception`，不再有
`on_node_start` / `on_task_success` 等逐个事件回调。

### 工作函数

- `fibonacci(n)`：**迭代**实现（`O(n)`），非递归；`n <= 0` 抛 `ValueError`，非 `int` 抛 `TypeError`
- `cpu_intensive(x)`：纯 CPU 循环，用于放大观察者开销；**当前脚本未在任何场景中调用**

## 可能出现的问题

1. **print 的 TTY 缓冲**：`print()` 默认行缓冲，当输出到实际终端时可能触发屏幕刷新，速度慢于重定向到文件。不同终端环境下 print 的开销可能有差异。
2. **tqdm 的 `total` 延迟创建**：`TqdmObserver` 在收到 `NodeStartEvent` 时创建进度条，在收到 `TaskInputEvent` 时累加总量（该事件可能先于 `NodeStartEvent` 到达，因此进度条未创建时只累加 `_total`）。由于 `run()` 会先注入全部任务再启动节点，`NodeStartEvent` 到达时 `total` 已包含启动前注入的任务数；后续若再有 `TaskInputEvent`，进度条会动态扩展，但不影响基准结果的正确性。
3. **热启动效应**：首次运行可能受字节码缓存预热、import 初始化或系统缓存影响，后续轮次会更快。`bench_observer_multirun()` 通过多轮取均值来缓解该问题。
4. **斐波那契负载本身太轻**：`fibonacci` 是迭代 `O(n)` 实现，`light_fib` 与 `heavy_fib` 的单任务耗时都在微秒级，测得的总耗时主要由框架调度、事件分发与 observer I/O 构成，而不是计算。两组数据的差异更多来自任务数量（10 vs 7），不能把 `heavy_fib` 解读为“计算占主导”。若要观察 observer 开销随单任务耗时的衰减，需要换成真正的毫秒级负载（如递归 fib 或加入 `time.sleep`）。

## 基准结果（实测）

> 🟢 本节各表格中的耗时均为历史实测数据，无法从源码验证，需人工确认。
>
> 这些数据采集于观察者仍使用逐事件回调的旧版本；当前实现已统一为 `on_event` + `match`，
> 事件分发开销与相对比例可能发生变化，建议在本地重新运行后再引用。

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

- 串行模式下，测量值主要由框架自身的调度与事件分发开销构成；`fibonacci` 是迭代 `O(n)`，`fib(50~80)` 也只有几十次循环，因此“轻量”和“较重”两组的单任务计算差异都在微秒级。
- **轻量任务**中，observer 带来的**相对差异**更明显（历史单轮数据里可达 ~50%），但方向并不稳定（print 甚至出现过负值）；绝对耗时只有毫秒级，单轮数值受测量噪声主导，应以多轮均值为准。
- **较重任务**（fib 50~80）的 7 个任务总耗时反而更低，主要是因为任务数更少，而不是“计算耗时占主导”；本脚本的两组负载都过于轻量，无法据此推出“单任务超过 1ms 后 observer 开销可忽略”的结论。
- 若需要评估真实业务负载下的 observer 开销，应改用毫秒级以上的单任务耗时，再对比三种场景。

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

- `celestialflow`（`Observer`、`PrintObserver`、`TaskExecutor`，以及 `celestialflow.observer` 下的各类事件类型）
- `tqdm`（`TqdmObserver` 使用）
