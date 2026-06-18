# bench/ 基准测试总览

> 📅 最后更新日期: 2026/06/18

## 说明

本目录收集 `CelestialFlow` 项目中的各类 benchmark 文档，覆盖执行模式、图调度、持久化、队列、哈希、锁开销、网络请求以及 Python 3.14 GIL / No-GIL 对比等主题。

这些 benchmark 的用途主要有三类：

- 为框架设计取舍提供量化依据
- 帮助用户根据任务类型选择合适的执行模式
- 记录不同实现策略在吞吐、延迟和资源开销上的差异

## 推荐阅读顺序

如果你想快速建立对项目性能特征的整体印象，建议按下面顺序阅读：

1. `bench_execution_mode.md`：先看单执行器在 `serial / thread / async` 下的差异
2. `bench_graph_mode.md`：再看任务图在不同 `stage_mode × execution_mode` 下的组合表现
3. `bench_gil_vs_nogil.md`：最后看 Python 3.14 free-threading 对 CelestialFlow 的影响

## 文档索引

### 执行模型与调度

| 文档 | 说明 |
|------|------|
| `bench_execution_mode.md` | `TaskExecutor` 在 `serial / thread / async` 下的性能对比 |
| `bench_graph_mode.md` | `TaskGraph` 在不同 `stage_mode × execution_mode` 组合下的性能对比 |
| `bench_gil_vs_nogil.md` | Python 3.14 GIL 与 No-GIL 环境下的 CelestialFlow 运行差异 |

### 网络与外部服务

| 文档 | 说明 |
|------|------|
| `bench_http_grpc.md` | CelestialTree 关闭 / HTTP / gRPC 三种追踪模式的开销对比 |
| `bench_requests.md` | Web API 请求基准测试 |

### 持久化与队列

| 文档 | 说明 |
|------|------|
| `bench_persistence_spout.md` | 持久化 spout 的日志 / fallback 写入性能 |
| `bench_queue.md` | 队列实现基准测试 |
| `bench_ipc_queue.md` | 进程间队列通信开销测试 |
| `bench_mpqueue_vs_shared_memory.md` | `multiprocessing.Queue` 与共享内存方案对比 |

### 数据结构与基础开销

| 文档 | 说明 |
|------|------|
| `bench_lock_overhead.md` | 锁竞争与同步开销 |
| `bench_datastructures.md` | 常见数据结构与跨进程结构性能基线 |
| `bench_hash.md` | `make_hashable` 等哈希相关方法对比 |
| `bench_hash_container.md` | 容器类对象哈希性能对比 |
| `bench_hash_memory.md` | 哈希相关实现的内存占用测试 |
| `bench_futures_memory.md` | futures 批量场景的内存开销 |
| `bench_tqdm.md` | 进度条输出开销测试 |
| `bench_utils.md` | benchmark 辅助统计工具说明 |

## 如何使用

大多数 benchmark 都可以直接从项目根目录运行，例如：

```bash
python bench/bench_execution_mode.py
python bench/bench_graph_mode.py
python bench/bench_gil_vs_nogil.py
```

其中 `bench_gil_vs_nogil.py` 需要分别在 GIL 与 No-GIL 解释器下各执行一次，具体运行方式请参考：

- `bench_gil_vs_nogil.md`

## 注意事项

1. 部分 benchmark 会依赖外部服务，例如 Reporter、CelestialTree 或特定 HTTP 接口。
2. 某些 benchmark 的耗时对本机负载、后台进程、电源策略和网络状态比较敏感，建议至少重复运行 3 次。
3. benchmark 的结论应结合任务类型理解，不能直接把某一场景的最优解推广到所有 workload。
