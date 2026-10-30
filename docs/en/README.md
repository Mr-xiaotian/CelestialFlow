# CelestialFlow — A Lightweight, Parallel, Graph-Based Python Task Scheduling Framework

> 📅 Last Updated: 2026/10/30

<p align="center">
  <img src="https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/logo.png" width="1080" alt="CelestialFlow Logo">
</p>

<p align="center">
  <a href="https://pypi.org/project/celestialflow/"><img src="https://badge.fury.io/py/celestialflow.svg"></a>
  <a href="https://pepy.tech/projects/celestialflow"><img src="https://static.pepy.tech/personalized-badge/celestialflow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/l/celestialflow.svg"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/pyversions/celestialflow.svg"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Task%20Graph-DAG-blueviolet">
  <img src="https://img.shields.io/badge/Workflow-Orchestrator-7c3aed">
  <img src="https://img.shields.io/badge/Event%20Tracing-CelestialTree-0ea5e9">
</p>

<p align="center">
  <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/README.md">中文</a> | <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/en/README.md">English</a> | <a href="https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/ja/README.md">日本語</a>
</p>

**CelestialFlow** is a lightweight yet fully-featured, graph-based Python task flow framework, suitable for medium-to-large Python task systems that require **complex dependencies**, **flexible execution models**, **cross-device execution**, and **observable execution traces**.

- Lighter and quicker to start than Airflow/Dagster
- More structured than multiprocessing/threading, capable of directly expressing complex dependency patterns such as loops and complete graphs

The basic unit of the framework is the **task node** (all uniformly inheriting from the internal base class `BaseTaskNode`). Three concrete node implementations are currently exposed; they can run independently or be connected to each other into a graph:

* **TaskExecutor** — General-purpose task executor
* **TaskSplitter** — Splits one input into multiple sub-tasks
* **TaskRouter** — Routes tasks to different downstreams based on conditions

All three node types support the following execution modes:

* **Serial**
* **Multi-threaded (thread)**
* **Coroutine (async)**

`TaskExecutor` supports custom skip functions (usable for task deduplication), failure retry, queue limits, and switching between multiple execution modes — it works well even when used standalone.

Nodes are connected to each other through **TaskGraph**, forming a task graph with upstream and downstream dependencies. A downstream node automatically receives the completed results from its upstream as input, creating a clear data flow. TaskGraph also provides preset topology structures such as `TaskChain` / `TaskCross` / `TaskGrid` / `TaskLoop` / `TaskWheel` / `TaskComplete` to quickly build common dependency patterns.

At the graph level, `graph_mode` uniformly controls how all nodes in the graph run:

* **Serial layout**: The current node finishes before the next node starts (downstream nodes may receive tasks early but will not execute immediately).
* **Thread layout**: The current node runs in an independent thread within the main process, suitable for I/O-intensive tasks and functions that cannot be pickled (such as lambda).
* **Async layout**: The current node runs as a coroutine, suitable for I/O-intensive asynchronous tasks.

`graph_mode` × `execution_mode` can be combined into 9 execution modes, covering the vast majority of scenarios.

TaskGraph can construct a full **Directed Graph** structure, supporting not only traditional Directed Acyclic Graphs (DAG), but also flexibly expressing **Tree**, **loop**, and even **Complete Graph** task dependencies.

Beyond execution and scheduling, CelestialFlow further introduces the **CelestialTree (ctree) event tracing system**, which records explicit causal relationships for each task and its derivative behaviors (success, failure, retry, split, routing, etc.). With ctree, you can start from any initial task and fully reconstruct its propagation path and execution trace within the TaskGraph, enabling complete **tracing, analysis, and interpretation** of the task system. Since 3.2.4, `ctree` uses a local ultra-simplified implementation by default and does not require the `celestialtree` external package; if gRPC remote tracing capability is needed, it can be additionally installed.

On this foundation, CelestialFlow provides event tracing, status reporting, persistent replay, and other features. The Web visualization interface is provided by the separate project [celestialflow-web](https://github.com/Mr-xiaotian/celestialflow-web), and the two collaborate via the HTTP protocol.

## Project Structure

```mermaid
flowchart LR

    %% ===== TaskGraph =====
    subgraph TG[TaskGraph]
        direction LR

        S1[TaskExecutor A]
        S2[TaskSplitter B]
        S3[TaskExecutor C]
        S4[TaskRouter D]

        S1 --> S2 --> S3 --> S1
        S1 --> S4

    end

    %% Style TaskGraph outer frame
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% Unified styling format
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% Style TaskNodes
    class S1,S2,S3,S4 blueNode;

    %% ===== Links =====
    TG --> CFB[CelestialFlow Web]
    CFB --> TG

    style CFB fill:#ffeaf0,stroke:#d66b8c,stroke-width:2px,rx:10px,ry:10px

```

## Quick Start

Install CelestialFlow:

```bash
# It is recommended to use `uv` for dependency and environment management
uv pip install celestialflow

# However, you can also use `pip` directly
pip install celestialflow
```

If you only need CelestialFlow's core scheduling, observability, and persistence capabilities, the above installation is sufficient.

If you also need to enable CelestialTree event tracing, you must **additionally install** `celestialtree`:

```bash
# For published package users
uv pip install celestialtree

# If you are a developer/contributor after cloning the repository
uv sync --group dev
```

A simple runnable example:

```python
from celestialflow import TaskExecutor, TaskGraph


def add(task):
    x, y = task
    return x + y


def square(x):
    return x**2


if __name__ == "__main__":
    # Define two task nodes
    executor_1 = TaskExecutor(
        name="Adder",
        func=add,
        execution_mode="thread",
        max_workers=4,
    )
    executor_2 = TaskExecutor(
        name="Squarer",
        func=square,
        execution_mode="thread",
        max_workers=4,
    )

    # Build the task graph structure
    graph = TaskGraph(name="DemoGraph", graph_mode="thread")
    graph.set_nodes(nodes=[executor_1, executor_2])
    graph.connect([executor_1], [executor_2])

    # Initialize tasks and start
    graph.run({"Adder": [(1, 2), (3, 4), (5, 6)]})
```

Note: Do not run in a `.ipynb` file.

👉 To see the full Quick Start, please refer to [Quick Start](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/quick_start.md)

## Further Reading

If you want to understand the overall architecture and core components of the framework, the following reference documents will help:

- [BaseTaskNode.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/node/core_node.md)
- [TaskExecutor.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/node/core_nodes.md)
- [TaskGraph.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/graph/core_graph.md)
- [MetricsObserver.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/observer/core_metrics.md)
- [TaskQueue.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/core_queue.md)
- [ReportConfig.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/core_config.md)
- [TaskStructure.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/graph/core_structure.md)
- [Observer.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/observer/core_observer.md)
- [Go Worker.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/go_worker.md)

Recommended reading order:

```mermaid
flowchart TD
    classDef core fill:#e6efff,stroke:#3b82f6,color:#1e3a8a;
    classDef runtime fill:#e9f8ef,stroke:#22c55e,color:#14532d;
    classDef structure fill:#fff6e6,stroke:#f59e0b,color:#78350f;
    classDef execution fill:#f3e8ff,stroke:#a855f7,color:#581c87;

    BTN[BaseTaskNode.md] --> TE[TaskExecutor.md] --> TG[TaskGraph.md]
    TE --> OB[Observer.md]
    TE --> TME[MetricsObserver.md]

    TG --> TQ[TaskQueue.md]
    TG --> TRC[ReportConfig.md]
    TG --> TSR[TaskStructure.md]

    TG --> GW[Go Worker.md]

    class BTN,TE,TG core;
    class TME runtime;
    class TSR structure;
    class TQ,GW execution;
    class TRC execution;
```

The following five can serve as supplementary reading:

- [UtilTypes.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_types.md)
- [UtilErrors.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_errors.md)
- [UtilFormat.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/runtime/util_format.md)
- [Lifecycle.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persist/core_lifecycle.md)
- [Log.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persist/core_log.md)

If you prefer to understand the framework's operation through a complete case study, refer to this tutorial on building a project from scratch with TaskGraph:

[📘 Case Tutorial](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/tutorial.md)

If you're interested in the `ctree_client` and its functionality added in version 3.0.7, take a look at this article:

[📚 CelestialTreeClient](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/ctree_client.md)

You can continue running more demo code. Here is a record of each demo file and descriptions of the demo functions within:

[🎮 demo/ Overview](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/demo/README.md)

If you want to run test code, you can first review the following documentation:

[🧪 tests/ Overview](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/tests/README.md)

If you want to view bench content, this data also serves as the basis for some of the framework's design decisions:

[⚡ bench/ Overview](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/bench/README.md)

## Requirements

**CelestialFlow** is based on Python 3.12+. The default runtime depends only on the most minimal core components.

| Dependency        | Description |
| ----------------- | ----------- |
| **Python ≥ 3.12** | Runtime environment; version 3.12 or above is recommended |
| **requests**      | HTTP client library, used for task status reporting and remote calls |

- `tqdm` is no longer a default runtime dependency (removed since 3.2.7). If you need to experience the `TaskProgress` progress bar in demos, you can `uv pip install tqdm` yourself.
- `celestialtree` is also **no longer a required dependency** (since 3.2.4): event tracing uses a local ultra-simplified implementation by default and can run with zero external dependencies. If gRPC remote tracing capability is needed, please additionally install `celestialtree`, or run `uv sync --group dev` in the source repository.
- The Redis nodes from old demo / bench have been removed in 3.2.4; the runtime of this project no longer depends on Redis.

- To use the visual web service, please go to the separate project [celestialflow-web](https://github.com/Mr-xiaotian/celestialflow-web) and install and run `celestialflow-web --host 0.0.0.0 --port 5000`.

## File Structure

```
📁 CelestialFlow	(560MB 757KB 428B)
    📁 bench           	(316KB 409B)
        📁 [1 excluded directory]                  	(193KB 163B)
        🐍 bench_datastructures.py          	(6KB 690B)
        🐍 bench_execution_mode.py          	(2KB 707B)
        🐍 bench_funnel_vs_lock.py          	(21KB 888B)
        🐍 bench_futures_memory.py          	(2KB 269B)
        🐍 bench_gil_vs_nogil.py            	(10KB 552B)
        🐍 bench_graph_mode.py              	(6KB 614B)
        🐍 bench_hash.py                    	(7KB 67B)
        🐍 bench_hash_container.py          	(3KB 1009B)
        🐍 bench_hash_memory.py             	(3KB 655B)
        🐍 bench_http_grpc.py               	(2KB 530B)
        🐍 bench_ipc_queue.py               	(7KB 104B)
        🐍 bench_lock_overhead.py           	(9KB 421B)
        🐍 bench_mpqueue_vs_shared_memory.py	(13KB 127B)
        🐍 bench_observer.py                	(7KB 58B)
        🐍 bench_persist_spout.py           	(4KB 323B)
        🐍 bench_queue.py                   	(5KB 857B)
        🐍 bench_requests.py                	(6KB 813B)
        🐍 bench_tqdm.py                    	(1KB 235B)
        🐍 bench_utils.py                   	(543B)
    📁 demo            	(811KB 650B)
        📁 [4 excluded directories]   	(755KB 996B)
        🐍 demo_executor.py  	(1KB 557B)
        🐍 demo_funnel.py    	(2KB 289B)
        🐍 demo_graph.py     	(2KB 975B)
        🐍 demo_network.py   	(3KB 756B)
        🐍 demo_nodes.py     	(3KB 915B)
        🐍 demo_observer.py  	(2KB 1004B)
        🐍 demo_redis.py     	(8KB 595B)
        🐍 demo_skip_dedup.py	(6KB 286B)
        🐍 demo_structure.py 	(8KB 448B)
        🐍 demo_utils.py     	(6KB 263B)
        🐍 demo_web.py       	(8KB 734B)
    📁 docs            	(2MB 88KB 855B)
        📁 en[collapsed]   	(678KB 928B)
        📁 ja[collapsed]   	(778KB 854B)
        📁 zh-CN[collapsed]	(679KB 97B)
    📁 experiments     	(3KB 21B)
        🐍 experiment_networkx.py	(1KB 908B)
        🐍 experiment_tqdm.py    	(1KB 137B)
    📁 img             	(5MB 871KB 242B)
        📷 file_structure.svg  	(4MB 918KB 1000B)
        📷 logo(old).png       	(836KB 542B)
        📷 logo.png            	(122KB 747B)
        📷 scc_condensation.svg	(17KB 1B)
    📁 src             	(1MB 661KB 60B)
        📁 celestialflow[collapsed]	(1MB 641KB 309B)
        📁 [1 excluded directory]      	(19KB 775B)
    📁 tests           	(3MB 65KB 73B)
        📁 assembly[collapsed]   	(42KB 929B)
        📁 benchmark[collapsed]  	(41KB 377B)
        📁 funnel[collapsed]     	(96KB 339B)
        📁 graph[collapsed]      	(803KB 239B)
        📁 node[collapsed]       	(510KB 93B)
        📁 observer[collapsed]   	(122KB 937B)
        📁 persist[collapsed]    	(186KB 828B)
        📁 persistence[collapsed]	(381KB 89B)
        📁 reporter[collapsed]   	(173KB 986B)
        📁 runtime[collapsed]    	(189KB 800B)
        📁 ticker[collapsed]     	(54KB 761B)
        📁 [3 excluded directories]    	(532KB 170B)
        🐍 conftest.py        	(1KB 693B)
    📁 [13 excluded directories]	(546MB 860KB 667B)
    ❓ .env            	(484B)
    ❓ .gitignore      	(1KB 315B)
    📝 AGENTS.md       	(2KB 800B)
    ❓ LICENSE         	(1KB 65B)
    ❓ Makefile        	(149B)
    ⚙️ pyproject.toml  	(2KB 624B)
    📝 README.md       	(16KB 321B)
    🔒 uv.lock         	(126KB 837B)
```
<p align="center">
  <em>celestial-flow 3.3.3</em>
</p>

(This view was generated by `inst_file.FileTree.print_tree()` from my other project [CelestialVault](https://github.com/Mr-xiaotian/CelestialVault). Conversion to an image was done with [Carbon](https://carbon.now.sh).)

## Version Log

- 3.3.3
  - feat:
    - Added `end_time` to `GraphEndEvent` / `NodeEndEvent`
    - Removed `class_name` from `GraphStartEvent`
  - refactor:
    - Removed some useless observer events, such as `on_worker_crash`
    - Moved log and reporter settings from `.toml` to runtime configuration
    - Removed some useless sqlite functions
  - fix:
    - Fixed the issue with graph analysis caching

For more past logs, see:

[change_log.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/change_log.md)

## Star History

If you are interested in the project, a star is welcome. If you have questions or suggestions, feel free to submit [Issues](https://github.com/Mr-xiaotian/CelestialFlow/issues) or let me know in [Discussions](https://github.com/Mr-xiaotian/CelestialFlow/discussions).

![Star History Chart](https://api.star-history.com/svg?repos=Mr-xiaotian/CelestialFlow&type=Date)

## License
This project is licensed under the MIT License - see the [LICENSE](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/LICENSE) file for details.

## Author
Author: Mr-xiaotian
Email: mingxiaomingtian@gmail.com
Project Link: [https://github.com/Mr-xiaotian/CelestialFlow](https://github.com/Mr-xiaotian/CelestialFlow)
