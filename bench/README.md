# Benchmarks

本目录包含 CelestialFlow 框架的性能基准测试脚本，用于评估各核心组件与底层机制的性能表现。

## 框架级基准测试

### bench_executor.py

对 `TaskExecutor` 进行基准测试，使用 `benchmark_executor` 工具比较 serial、thread、async 三种执行模式在 Fibonacci 计算任务下的性能差异。

### bench_graph.py

对 `TaskGraph` 进行基准测试，使用 `benchmark_graph` 工具在多节点 DAG 结构下测量图调度与执行的整体性能。

### bench_http_grpc.py

对比 CelestialTree 事件追踪在 HTTP 与 gRPC 两种传输协议下的性能差异，使用 `TaskSplitter + TaskChain` 结构测试大量任务的事件上报吞吐量。

## 底层机制基准测试

### bench_queue.py

对比 `threading.Queue`、`multiprocessing.Queue`、`Manager().Queue()` 和 Redis 队列在 put/get/qsize 操作上的性能差异。

### bench_ipc_queue.py

深入对比多种 IPC 队列实现（`MPQueue`、`SimpleQueue`、`Manager().Queue()`、`Pipe`）的吞吐量，支持不同 payload 大小和多轮重复测试。

### bench_mpqueue_vs_shared_memory.py

对比 `multiprocessing.Queue` 与 `SharedMemory` 环形缓冲区在进程间通信中的性能表现。

### bench_datastructures.py

对比多种跨进程数据结构（`MPQueue`、`Manager().list()`、`Manager().dict()`、`Value`、Redis）的读写性能。

### bench_hash.py

对比多种对象哈希算法（`pickle+md5`、`json+sha256`、`repr+hash` 等）在不同数据类型和大小下的性能与碰撞率。

### bench_requests.py

对比 `requests` 库在使用/不使用 Session、单线程/多线程并发场景下的 HTTP 请求性能。

### bench_tqdm.py

测量启用 `tqdm` 进度条对大量数据处理的性能开销。

## 工具

### bench_utils.py

基准测试的通用工具函数，提供 `summarize()` 用于汇总多轮测试的均值、标准差和吞吐量。
