# bench/ Benchmark Overview

> 📅 Last Updated: 2026/06/22

## Description

This directory collects benchmark documentation for various aspects of the `CelestialFlow` project, covering topics such as execution modes, graph scheduling, persistence, queues, hashing, lock overhead, network requests, and Python 3.14 GIL / No-GIL comparisons.

These benchmarks serve three main purposes:

- Provide quantitative evidence for framework design trade-offs
- Help users choose the appropriate execution mode based on task type
- Document differences in throughput, latency, and resource overhead across implementation strategies

## Recommended Reading Order

To quickly build a general impression of the project's performance characteristics, we recommend reading in the following order:

1. `bench_execution_mode.md`: First, see the differences of a single executor under `serial / thread / async`
2. `bench_graph_mode.md`: Then, see the combined performance of task graphs under different `stage_mode × execution_mode` combinations
3. `bench_gil_vs_nogil.md`: Finally, see the impact of Python 3.14 free-threading on CelestialFlow

## Document Index

### Execution Models and Scheduling

| Document | Description |
|------|------|
| `bench_execution_mode.md` | Performance comparison of `TaskExecutor` under `serial / thread / async` |
| `bench_graph_mode.md` | Performance comparison of `TaskGraph` under different `stage_mode × execution_mode` combinations |
| `bench_gil_vs_nogil.md` | CelestialFlow runtime differences under Python 3.14 GIL vs. No-GIL environments |

### Networking and External Services

| Document | Description |
|------|------|
| `bench_http_grpc.md` | Overhead comparison of CelestialTree in closed / HTTP / gRPC tracing modes |
| `bench_requests.md` | Web API request benchmarks |

### Persistence and Queues

| Document | Description |
|------|------|
| `bench_persistence_spout.md` | Log / fallback write performance for persistence spouts |
| `bench_queue.md` | Queue implementation benchmarks |
| `bench_ipc_queue.md` | Inter-process queue communication overhead tests |
| `bench_mpqueue_vs_shared_memory.md` | Comparison of `multiprocessing.Queue` vs. shared memory approaches |

### Data Structures and Base Overhead

| Document | Description |
|------|------|
| `bench_lock_overhead.md` | Lock contention and synchronization overhead |
| `bench_datastructures.md` | Performance baselines for common data structures and cross-process structures |
| `bench_hash.md` | Comparison of object stable hash strategies (`normalize_for_hash` + multiple serialization/hash combinations) |
| `bench_hash_container.md` | Hash performance comparison for container-type objects |
| `bench_hash_memory.md` | Memory usage tests for hash-related implementations |
| `bench_futures_memory.md` | Memory overhead for batch futures scenarios |
| `bench_tqdm.md` | Progress bar output overhead tests |
| `bench_utils.md` | Benchmark auxiliary statistics utility documentation |

## How to Use

Most benchmarks can be run directly from the project root directory, for example:

```bash
python bench/bench_execution_mode.py
python bench/bench_graph_mode.py
python bench/bench_gil_vs_nogil.py
```

`bench_gil_vs_nogil.py` needs to be executed once each under GIL and No-GIL interpreters. For specific execution instructions, refer to:

- `bench_gil_vs_nogil.md`

## Notes

1. Some benchmarks depend on external services, such as Reporter, CelestialTree, or specific HTTP interfaces.
2. The runtime of certain benchmarks is sensitive to local machine load, background processes, power policies, and network conditions; it is recommended to run at least 3 repetitions.
3. Benchmark conclusions should be understood in the context of the task type; the optimal solution for one scenario should not be directly generalized to all workloads.
