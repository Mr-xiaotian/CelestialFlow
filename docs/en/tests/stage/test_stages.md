# Specialized Stage Tests (test_stages.py)

> 📅 Last Updated: 2026/06/11

## Purpose
Validates the specialized task nodes (`TaskSplitter`, `TaskRouter`) in `celestialflow.stage.core_stages`, ensuring tasks can be correctly split, routed, and dispatched.

## Core Test Targets
- `TaskSplitter`: A node that splits a single task result into multiple subtasks.
- `TaskRouter`: A router that directs tasks to specific downstream nodes based on predefined rules.

## Key Test Scenarios

### `TestTaskSplitter` — Task Splitter
| Case | Coverage Goal |
|------|----------|
| `test_splitter_init` | Validates default serial mode, no retry, initial counter is 0 |
| `test_splitter_process_success` | After successful execution in a `TaskGraph`, downstream receives 3 independent tasks; `split_counter` count is correct |
| `test_splitter_allows_empty_iterable` | Empty iterable input produces 0 subtasks without raising an exception |
| `test_splitter_supports_generator_input` | Single-use iterator (generator) input still correctly splits and dispatches all subtasks |
| `test_splitter_allows_constructor_split_item` | Inject transform logic for a single subtask via the `split_item` constructor parameter |

### `TestTaskRouter` — Task Router
| Case | Coverage Goal |
|------|----------|
| `test_router_init` | Validates default serial mode, no retry, route counters are an empty dict |
| `test_router_route_logic` | Validates `_route` correctly parses `(target, data)` tuples; unknown target raises `InvalidOptionError`; non-tuple format raises `TaskFormatError` |
| `test_router_process_success` | After successful routing in a `TaskGraph`, `route_counters` counts are correct and target nodes each receive the corresponding number of successful tasks |

## Test Focus
- **One-to-many propagation**: Validates that the Splitter's result list is expanded into multiple independent task envelopes, not broadcast as the same result.
- **Named dispatch**: Validates that the Router precisely directs tasks to specified downstream nodes via a pre-binding mechanism.
- **State tracking**: Validates that the custom internal counters (`split_counter`, `route_counters`) of specialized nodes accurately reflect business logic execution.

## How to Run

```bash
# Run all
pytest tests/stage/test_stages.py -v

# Run TaskSplitter tests only
pytest tests/stage/test_stages.py -k "splitter" -v

# Run TaskRouter tests only
pytest tests/stage/test_stages.py -k "router" -v
```

## Performance Reference

| Test | Duration |
|------|------|
| `TestTaskSplitter` | ~0.2s |
| `TestTaskRouter` | ~0.2s |

## Important Details
- Tests use `TaskGraph.connect()` and `TaskGraph.start_graph()` to construct a real graph execution environment for verification, rather than using mock queues to intercept output.
- Built-in `split_counter` and `route_counters` are automatically maintained by the internal mechanisms of the specialized Stages.

## Notes
- Specialized stages are commonly used for data splitting and dynamic parallelism adjustment in complex workflows.
- Related implementation is in `src/celestialflow/stage/core_stages.py`.
