# CelestialTree Client

> 📅 Last Updated: 2026/04/22

CelestialFlow integrates a `celestialtree` client for fine-grained full-chain task tracing (Provenance) and event recording.

## Introduction

CelestialTree is an independent event sourcing system. CelestialFlow uses `CelestialTreeClient` to send key events during a task's lifecycle (input, success, failure, retry, split, route, etc.) to the CelestialTree service.

This allows users to:
1. **Track Data Lineage**: Query which original task produced a given result and through which steps.
2. **Locate Error Root Causes**: Query the upstream source of a failed task.
3. **Visualize Execution Trees**: Generate call trees of task execution.

## Configuration

Configure during `TaskGraph` initialization:

```python
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)
```

## Event Types

The framework automatically emits the following event types:

- `task.input`: Task enters a Stage.
- `task.success`: Task processed successfully.
- `task.error`: Task processing failed.
- `task.retry.N`: Task retry number N.
- `task.split`: Task split.
- `task.route`: Task routed.
- `task.duplicate`: Duplicate task detected.
- `termination.input` / `termination.merge`: Termination signal flow.

## Provenance Queries

`TaskGraph` provides simplified wrapper methods for querying provenance information:

### get_stage_input_trace

Retrieves the provenance tree for all current input tasks of a given Stage (i.e., where each task originated from).

```python
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
print(trace_str)
```

### get_error_trace

Retrieves the provenance tree for a specific error ID.

```python
trace_str = graph.get_error_trace(error_id=12345)
print(trace_str)
```
