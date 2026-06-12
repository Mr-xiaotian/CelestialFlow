# CelestialTree Client

> 📅 Last Updated: 2026/04/22

CelestialFlow integrates the `celestialtree` client to implement fine-grained full-chain task provenance tracking and event recording.

## Introduction

CelestialTree is an independent event provenance system. CelestialFlow uses `CelestialTreeClient` to send key events in the task lifecycle (input, success, failure, retry, split, route, etc.) to the CelestialTree service.

This enables users to:
1. **Trace data lineage**: Query which original task, through which steps, generated a particular result.
2. **Locate error root causes**: Query the upstream source of a failed task.
3. **Visualize execution trees**: Generate the call tree of task execution.

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

The framework automatically emits the following types of events:

- `task.input`: Task enters a Stage.
- `task.success`: Task processed successfully.
- `task.error`: Task processing failed.
- `task.retry.N`: Task retry attempt N.
- `task.split`: Task split.
- `task.route`: Task routed.
- `task.duplicate`: Duplicate task detected.
- `termination.input` / `termination.merge`: Termination signal propagation.

## Provenance Queries

`TaskGraph` provides simplified wrapper methods for querying provenance information:

### get_stage_input_trace

Get the provenance tree for all current input tasks of a Stage (i.e., where these tasks came from).

```python
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
print(trace_str)
```

### get_error_trace

Get the provenance tree for a specific error ID.

```python
trace_str = graph.get_error_trace(error_id=12345)
print(trace_str)
```
