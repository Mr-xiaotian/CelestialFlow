# CelestialTree Client

> 📅 Last Updated: 2026/09/24

CelestialFlow supports integrating the `celestialtree` client for fine-grained full-chain task provenance tracking and event recording.

> `celestialtree` has now been removed from CelestialFlow's default runtime dependencies.
> If you need the tracing capabilities described on this page, install `celestialtree` separately, or run `uv sync --group dev` in the source repository.

## Introduction

CelestialTree is an independent event provenance system. CelestialFlow uses `CelestialTreeClient` to send key events in the task lifecycle (input, success, failure, retry, split, route, etc.) to the CelestialTree service.

This enables users to:
1. **Trace data lineage**: Query which original task, through which steps, generated a particular result.
2. **Locate error root causes**: Query the upstream source of a failed task.
3. **Visualize execution trees**: Generate the call tree of task execution.

## Installation

```bash
# If celestialflow is already installed, just supplement with CelestialTree
uv pip install celestialtree

# If you are developing/running demos in the source repository
uv sync --group dev
```

## Configuration

The current `TaskGraph.set_ctree()` accepts an event client instance, rather than the legacy `use_ctree=True` / `host=...` format.

Configure after `TaskGraph` initialization:

```python
from celestialtree import Client as CelestialTreeClient

ctree_client = CelestialTreeClient(
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
)

graph.set_ctree(ctree_client)
```

## Event Types

The framework automatically emits the following types of events:

- `task.input`: Task enters a Stage.
- `task.success`: Task processed successfully.
- `task.error`: Task processing failed.
- `task.retry.N`: Task retry attempt N.
- `termination.input` / `termination.merge`: Termination signal propagation.

## Provenance Queries

`TaskGraph` no longer provides built-in convenience query methods such as `get_stage_input_trace` / `get_error_trace`; the framework is only responsible for sending events to the CelestialTree service through the injected client. When you need to query provenance information, use the query interfaces of the `celestialtree` client itself directly.
