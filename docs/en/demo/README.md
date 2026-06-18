# demo/ Demo Overview

> 📅 Last Updated: 2026/06/18

## Description

This directory collects Chinese documentation for various demo scripts under `demo/`, helping you quickly understand CelestialFlow's core capabilities, graph structure representation, execution modes, observers, Redis integration, and common utility functions.

These demos lean more towards "hands-on experience" and "capability showcase", distinct from `bench/`'s performance comparisons and `tests/`'s behavioral verification.

## Recommended Reading Order

If this is your first encounter with the project, we recommend reading in the following order:

1. `demo_executor.md`: First understand the basic execution modes of `TaskExecutor`
2. `demo_graph.md`: Then see how `TaskGraph` connects stages into a DAG
3. `demo_structure.md`: Continue with structured wrappers like chains, grids, rings, and complete graphs
4. `demo_observer.md`: Finally, see observation and progress display during execution

## Document Index

### Execution and Task Graphs

| Document | Description |
|------|------|
| `demo_executor.md` | Serial / thread / async execution demos for `TaskExecutor` |
| `demo_graph.md` | DAG task graph, ETL pipeline, and staged/eager scheduling demos |
| `demo_structure.md` | `TaskChain`, `TaskCross`, `TaskGrid`, `TaskLoop` and other structured graph wrapper demos |
| `demo_stages.md` | `TaskStage`, `TaskSplitter`, `TaskRouter` and other stage-level capability descriptions |

### Observation, Pipelines, and Extensions

| Document | Description |
|------|------|
| `demo_observer.md` | Observer, progress reporting, and lifecycle callback demos |
| `demo_funnel.md` | Inlet / Spout pipeline behavior and data flow demos |
| `demo_redis.md` | Redis-related integration examples |

### Utility Functions

| Document | Description |
|------|------|
| `demo_utils.md` | Common utility functions, input construction, and task function descriptions used in demos |

## How to Use

Most demos can be run directly from the project root directory, for example:

```bash
python demo/demo_executor.py
python demo/demo_graph.py
python demo/demo_structure.py
```

Some demos require additional environments, such as:

- Reporter service
- Redis service
- CelestialTree service

Please check the "Dependencies" and "How to Run" sections in the corresponding page documentation before running.

## Notes

1. Demos aim to showcase capabilities and do not necessarily pursue minimal dependencies or shortest runtime.
2. Some examples connect to external services; if environment variables or the server side are not ready, they will fail directly at runtime.
3. If you want to verify framework behavioral correctness, refer to `tests/` first; if you want to evaluate performance trade-offs, refer to `bench/` first.
