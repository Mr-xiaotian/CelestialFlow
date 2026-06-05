# Specialized Stage Tests (test_stages.py)

> Last Updated: 2026/05/23

## Purpose
Validates the specialized task nodes in `celestialflow.stage.core_stages`, namely Splitter and Router, ensuring tasks are split, routed, and distributed correctly.

## Key Test Objects
- `TaskSplitter`: A node that splits one task result into multiple child tasks.
- `TaskRouter`: A router that sends tasks to specific downstream nodes according to predefined rules.

## Key Test Flow
1. **TaskSplitter**:
   - **Initialization**: Verifies the default mode is serial and retries are disabled.
   - **Split logic**: Simulates a successful execution returning `[1, 2, 3]`, then verifies that 3 independent task envelopes are produced in the output queue and that `split_counter` is updated correctly.
2. **TaskRouter**:
   - **Routing rules**: Verifies that `_route` handles `(target, data)` tuples correctly and extracts both the target name and payload.
   - **Dispatch verification**: Verifies that tasks enter the correct named downstream queue, such as `q_target1` for `target1`, and that the corresponding route counter increases.
   - **Exception handling**: Verifies that malformed input such as a non-tuple or an unknown target raises `TaskFormatError` or `InvalidOptionError`.

## Test Focus
- **One-to-many propagation**: Verifies whether Splitter produces newly split envelopes rather than simple broadcasts.
- **Named dispatch**: Verifies that Router uses the named-send capability of `TaskOutQueue` for precise routing.
- **State tracking**: Verifies that internal counters such as `split_counter` and `route_counters` accurately reflect business behavior.

## How to Run

```bash
# Run all tests
pytest tests/stage/test_stages.py -v

# Run TaskSplitter tests only
pytest tests/stage/test_stages.py -k "splitter" -v
pytest tests/stage/test_stages.py -k "Splitter" -v

# Run TaskRouter tests only
pytest tests/stage/test_stages.py -k "router" -v
pytest tests/stage/test_stages.py -k "Router" -v
```

## Performance Reference

| Test | Duration |
|------|----------|
| `TestSplitter` | ~0.2s |
| `TestRouter` | ~0.2s |

## Important Details
- The tests use mocked `TaskOutQueue` setup to intercept output data for verification.
- They also depend on the `log_inlet` fixture for asynchronous error logging.

## Notes
- Specialized stages are commonly used for data sharding and dynamic parallelism in complex workflows.
- Related implementation: `src/celestialflow/stage/core_stages.py`.

