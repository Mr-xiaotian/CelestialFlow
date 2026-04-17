# test_executor.py

本文件用于测试 CelestialFlow 框架中 **TaskExecutor** 的基本功能与运行模式。

**TaskExecutor** 是 CelestialFlow 框架中最基础的任务执行单元，在本测试中，它以**独立运行模式（Standalone Mode）**运行，与作为节点被嵌入到 **TaskGraph** 中的"stage 模式"不同。

在独立模式下，TaskExecutor 自行负责任务调度、异常重试、计数与并发控制，无需依赖图结构即可完成完整的任务生命周期管理。

本测试文件通过递归计算 Fibonacci 数列的示例函数，验证了 TaskExecutor 在 **单线程（serial）**、**多线程（thread）** 与 **异步（async）** 三种执行模式下的正确性、稳定性与性能表现。

## test_fibonacci_serial()

测试 **TaskExecutor** 在串行执行模式下的运行行为。

- **任务函数**：`fibonacci(n)`（递归计算第 n 个 Fibonacci 数）
- **运行模式**：`serial`
- **测试特性**：
  - 输入数据包含非法值（`0`、`None`、空字符串），用于验证异常捕获与重试逻辑；
  - 设置 `max_retries=1`，并允许对 `ValueError` 异常进行重试。

## test_fibonacci_thread()

测试 **TaskExecutor** 在多线程执行模式下的运行行为。

- **任务函数**：`fibonacci(n)`
- **运行模式**：`thread`（6 个工作线程）
- **测试特性**：与串行模式相同的数据输入与错误设计。

## test_fibonacci_async()

测试 TaskExecutor 在异步模式下的行为。

- **任务函数**：`fibonacci_async(n)`（递归计算的异步版本）
- **执行模式**：`async`（协程并发执行）
- **测试特性**：
  - 与同步测试相同的数据输入与错误设计；
  - 使用 `await executor.start_async()` 启动任务。

运行方式：
```bash
pytest tests/test_executor.py
```

或单独运行异步测试：

```bash
pytest tests/test_executor.py::test_fibonacci_async
```

# test_stages.py

该文件主要用于测试 [core_stages.py](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/src/celestialflow/stage/core_stages.py) 中定义的特殊节点 `TaskSplitter`、`TaskRouter`、`TaskRedis*`，它们都继承自 `TaskStage`。

`TaskSplitter` 用于将迭代器形式的多个任务数据(List[Task])拆成单独任务(Task)传给下游，因此在 Web 页面可以看到 `TaskSplitter` 下游获取的数据会比 `TaskSplitter` 处理成功的数据更多；`TaskRouter` 用于根据路由函数将任务分发到不同的下游节点；`TaskRedisTransport` 用于将传入的任务传给 Redis, 如果此时开启 go_worker，go_worker 会从 Redis 中接受数据并在处理后将答案传回 Redis，之后 `TaskRedisAck` 再提取答案并传给下游；如果想直接从 Redis 中重新读取任务, 可以使用 `TaskRedisSource`, 一般用于跨设备/跨 TaskGraph 传输任务。

对于这些节点更详细的描述请看 [core_stages.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/stage/core_stages.md)。

## test_splitter_0()

模拟了一次爬虫行为，包括爬取网页文件、记录爬取信息、处理网页信息、下载网页中的额外内容(图片视频等)同时在当前页面解析其他需要爬取的页面。构建了一个包含环形依赖的复杂图结构。

## test_splitter_1()

这个测试函数模拟了一个特殊的情况: 有时候输入 root 节点的任务数过大, 比如 `range(int(1e5))`。为了解决这个问题可以在最初放一个 `TaskSplitter` 节点, 给它传被列表打包的任务组，这样下游就可以不断接受并处理上游的数据。

## test_redis_ack_0()

对比了计算 fibonacci 时，直接用 Python 计算与使用 Redis 外接 go_worker 计算间的时间差异。从结果来看，即便 Redis 传输耗费了大量时间，但 Go 强大的性能依旧让使用 go_worker 成为 CPU 密集计算时的好选择。

需要注意的是, 在使用外部节点 `Go Worker` 系列节点前需要进行[前期设置](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期设置)。

## test_redis_ack_1()

测试了传递多参数的情景，同时也可以直观看出对于 `sum` 这种几乎 0 运算时间的函数，使用 Redis 的通信消耗会远远超过 Go 高性能省下的时间。

## test_redis_ack_2()

测试了进行网络请求并下载数据时使用 Python 原生函数与 go_worker 的差距。

## test_redis_source_0()

测试了 `TaskRedisSource` 从 Redis 中重新读取任务的能力，用于跨设备/跨 TaskGraph 传输任务的场景。

## test_router_0()

测试了 `TaskRouter` 的路由功能，将任务根据路由规则分发到不同的下游节点（Stage A 和 Stage B）。

# test_structure.py

该文件主要用于测试 [core_structure.py](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/src/celestialflow/graph/core_structure.py) 中预设的几种图结构，包括作为无环图(DAG)的:

- TaskChain: 所有节点串联
- TaskCross: Graph 分为多层, 每一层有多个节点。每一层内部节点互不相连, 同时链接下一层所有节点。
- TaskGrid: 节点成网格状, 从左上角的节点开始, 每一个节点与下/右侧节点相连。

作为有环图的:

- TaskLoop: 类似 TaskChain. 只是首位相连。
- TaskWheel: 在 TaskLoop 的基础上存在一个中心节点, 中心节点连向其他每一个节点。
- TaskComplete: 完全图, 所有节点两两相连。

对于结构详细的描述请看 [core_structure.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/graph/core_structure.md)。

除了 `core_structure.py` 中预设的几种结构, 还包括类似:

- forest: 多个互不相关的 Tree 状结构, 用 TaskGraph 实现
- star: 一个 root 节点指向多个互不关联的节点, 用 TaskCross 实现
- fanin: 多个 root 节点指向一个节点, 用 TaskCross 实现
- network: 多层多分支的 DAG 结构
