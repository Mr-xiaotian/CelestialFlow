# test_executor.py

本文件用于测试 CelestialFlow 框架中 **TaskExecutor** 的基本功能与运行模式。

**TaskExecutor** 是 CelestialFlow 框架中最基础的任务执行单元，在本测试中，它以**独立运行模式（Standalone Mode）**运行，与作为节点被嵌入到 **TaskGraph** 中的“stage 模式”不同。

在独立模式下，TaskExecutor 自行负责任务调度、异常重试、计数与并发控制，无需依赖图结构即可完成完整的任务生命周期管理。

本测试文件通过递归计算 Fibonacci 数列的示例函数，验证了 TaskExecutor 在 **单线程（serial）**、**多线程（thread）**、**多进程（process）** 与 **异步（async）** 四种执行模式下的正确性、稳定性与性能表现。

## test_executor()

测试 **TaskExecutor** 在同步执行环境中的运行行为。

- **任务函数**：`fibonacci(n)`（递归计算第 n 个 Fibonacci 数）
- **运行模式**：单线程、线程池、多进程（通过 `executor.test_methods()` 自动测试三种模式）
- **测试特性**：
  - 输入数据包含非法值（`0`、`None`、空字符串），用于验证异常捕获与重试逻辑；
  - 设置 `max_retries=1`，并允许对 `ValueError` 异常进行重试；
  - 启用进度条显示与日志记录。
- **主要验证点**：
  1. 各执行模式下任务调度与计数逻辑是否一致；
  2. 异常任务能否被正确识别与重试；
  3. `test_methods()` 是否能准确统计不同模式下的执行时间与性能差异。

## test_executor_async()

测试 TaskExecutor 在异步模式下的行为。

- **任务函数**：`fibonacci_async(n)`（递归计算的异步版本）
- **执行模式**：`async`（协程并发执行）
- **任务特性**：
  - 与同步测试相同的数据输入与错误设计；
  - 使用 `await executor.start_async()` 启动任务；
  - 记录整个任务批次的总执行时间。
- **主要验证点**：
  1. 异步任务能否在高并发下正确完成；
  2. 异常捕获与重试机制是否在协程环境下正常；
  3. 异步执行相对于同步执行的性能对比。

运行方式：
```bash
pytest tests/test_manage.py
```

或单独运行异步测试：

```bash
pytest tests/test_manage.py::test_executor_async
```

# test_nodes.py

该文件主要用于测试[task_nodes.py](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/src/celestialflow/task_nodes.py)中定义的两个特殊节点 `TaskSplitter` 与 `TaskRedis*`，两者都继承自 `TaskStage`。

`TaskSplitter`用于将迭代器形式的多个任务数据(List[Task])拆成单独任务(Task)传给下游，因此在 Web 页面可以看到 `TaskSplitter` 下游获取的数据会比 `TaskSplitter` 处理成功的数据更多； `TaskRedisSink` 用于将传入的任务传给 Redis, 如果此时开启go_worker，go_worker会从 Redis 中接受数据并在处理后将答案传回 Redis，之后 `TaskRedisAck` 再提取答案并传给下游； 如果想直接从 Redis 中重新读取任务, 可以使用`TaskRedisSource`, 一般用于跨设备/跨TaskGraph传输任务。

对于两节点更详细的描述请看[task_nodes.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/task_nodes.md)。

## test_splitter_0() 与 test_splitter_1()

这两个测试文件处理的是同一个Graph结构，模拟了一次爬虫行为，包括爬取网页文件、记录爬取信息、处理网页信息、下载网页中的额外内容(图片视频等)同时在当前页面解析其他需要爬取的页面。

两者不同之处在于test_splitter_0()使用test_methods测试了所有的运行模式，这在添加新特性时时有用的，正常只需要运行test_splitter_1()。

## test_splitter_2()

这个测试函数模拟了一个特殊的情况: 有时候输入root节点的任务数过大, 比如range(int(1e10)), 那么所有节点都会一直等待, 这是因为当前`task_graph.put_stage_queue`的运行机制。为了解决这个问题可以在最初放一个 `TaskSplitter` 节点, 给它传被列表打包的任务组，这样下游就可以不断接受并处理上游的数据，即便数据量非常庞大(比如`range(int(1e8))`)。

运行这个测试函数时可能出现stage 2已经处理所有任务，但程序没有中止的情况，这是因为 `task_logging` 设计中日志记录与写入文件是分离的，当stage 2处理完任务时日志还没有被全部写入文件，等待片刻就好。

## test_redis_ack_0()

这个测试文件对比了计算fibonacci时，直接用py计算与使用Redis外接go_worker计算间的时间差异。从结果来看，即便Redis传输耗费了大量时间，但Go强大的性能依旧让使用go_worker成为CPU密集计算时的好选择。

需要注意的是, 在使用外部节点 `Go Worker` 系列节点前需要进行[前期设置](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/go_worker.md#前期设置)。

## test_redis_1()

这个测试文件测试了传递多参数的情景，同时也可以直观看出对于 `sum` 这种几乎0运算时间的函数，使用 Redis 的通信消耗会远远超过Go高性能省下的时间。

## test_redis_2()

这个测试函数测试了进行网络请求并下载数据时使用python原生函数与go_worker的差距。

# test_structur.py

该文件主要用于测试[task_structure.py](..\src\celestialflow\task_structure.py)中预设的几种图结构，包括作为无环图(DAG)的:

- TaskChain: 所有节点串联
- TaskCross: Graph 分为多层, 每一层有多个节点。每一层内部节点互不相连, 同时链接下一层所有节点。
- TaskGrid: 节点成网格状, 从左上角的节点开始, 每一个节点与下/右侧节点相连。

作为有环图的:

- TaskLoop: 类似TaskChain. 只是首位相连。
- TaskWheel: 在TaskLoop的基础上存在一个中心节点, 中心节点连向其他每一个节点。
- TaskComplete: 完全图, 所有节点两两相连。

对于结构详细的描述请看[Src README.md](..\src\celestialflow\README.md)。

除了 `task_structure.py` 中预设的几种结构, 还包括类似:

- forest: 多个互不相关的 Tree 状结构, 用 TaskGraph 实现
- star: 一个root节点指向多个互不关联的节点, 用TaskCross实现
- fanin: 多个root节点指向一个节点, 用TaskCross实现

