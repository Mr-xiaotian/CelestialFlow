# Reporter Injection and Push Tests (test_reporter.py)

> 📅 Last Updated: 2026/08/19

## Purpose

Validates the task injection and error push logic of `TaskReporter` in `celestialflow.observability.core_report`: after the Reporter pulls split tasks and termination signal payloads from the remote, it verifies that the tasks and termination signals are correctly injected to the corresponding stages via `put_task` / `put_signal` respectively; also validates the endpoint selection for error push and the incremental push behavior based on the server-side watermark.

## Core Test Objects

| Class | Type | Description |
|----|------|------|
| `FakeResponse` / `FakePostResponse` | Mock | Simulates HTTP GET/POST responses |
| `FakeSession` / `FakePushSession` | Mock | Simulates `requests.Session` GET/POST methods and records calls |
| `FakeTaskGraph` / `FakeErrorGraph` | Mock | Simulates graph injection interface and error query interface |
| `FakeLogInlet` | Mock | Records logs for injection success/failure, pull failure, and push failure |
| `TaskReporter` | Class Under Test | The injector and reporter in `celestialflow.observability` |

## Key Test Scenarios

### `test_reporter_accepts_split_task_and_termination_payload`

**Coverage Goal**: Validates that `TaskReporter._pull_injection()` can consume the split payload `{"tasks": {...}, "terminations": [...]}` returned by the server, and inject the tasks and termination signals to the corresponding stages via `put_task` / `put_signal` respectively.

**Assertion Intent**:

- `StageA`'s `task_calls` contains one task batch `[1, 2, 3]`, and `signal_calls` is 0.
- `StageB`'s `task_calls` is empty, but `signal_calls` is 1 (only the termination signal is injected).
- `log_inlet.successes` records two success logs: task injection for StageA `(StageA, [1, 2, 3])` and termination signal injection for StageB `(StageB, [TERMINATION_SIGNAL])`.
- No failure logs (`failures` and `pull_failures` are both empty).

```mermaid
sequenceDiagram
    participant R as TaskReporter
    participant S as FakeSession
    participant G as FakeTaskGraph
    participant L as FakeLogInlet

    R->>S: GET /api/pull_injection
    S-->>R: {"tasks": {"StageA": [1,2,3]}, "terminations": ["StageB"]}
    R->>R: Split tasks and terminations
    R->>G: put_task([1, 2, 3]) → StageA
    R->>G: put_signal() → StageB
    G-->>R: Record task_calls / signal_calls
    R->>L: inject_tasks_success("StageA", [1, 2, 3])
    R->>L: inject_tasks_success("StageB", [TERMINATION_SIGNAL])
```

### `test_reporter_merges_tasks_and_termination_for_same_stage`

**Coverage Goal**: When the same node appears in both `tasks` and `terminations`, the task list should be retained, and an additional `put_signal()` should be sent on that node, rather than overwriting each other.

**Assertion Intent**:

- `StageA`'s `task_calls` contains only `[1, 2, 3]` (tasks and termination signal call `put_task` / `put_signal` respectively), and `signal_calls` is 1.
- `log_inlet.successes` contains two records: first `(StageA, [1, 2, 3])` (task injection), then `(StageA, [TERMINATION_SIGNAL])` (termination signal injection).

### `test_reporter_pushes_errors_via_push_errors_endpoint_only`

**Coverage Goal**: Validates that `TaskReporter._push_errors()` only pushes errors via the `/api/push_errors` endpoint (no longer using the old `/api/push_errors_meta`).

- Writes one sqlite error record.
- Sets `_server_has_current_graph = False` (triggers full push).
- Asserts the POST target URL ends with `/api/push_errors`.
- Asserts the payload contains `graph_id` and `errors` fields, and the error record fields match the sqlite record.

### `test_reporter_pushes_only_errors_after_server_max_event_id`

**Coverage Goal**: Validates that the Reporter only pushes failed records whose `event_id` is greater than the server's watermark.

- Writes 3 error records (`event_id=1,5,7`).
- Sets `_server_has_current_graph = True`, `_server_max_event_id_in_fail = 3`.
- Asserts that only records with `event_id` 5 and 7 are pushed.

## Test Coverage Matrix

| Test Function | Coverage Target |
|----------|----------|
| `test_reporter_accepts_split_task_and_termination_payload` | Split payload parsing, merged task and termination injection, injection success logging |
| `test_reporter_merges_tasks_and_termination_for_same_stage` | Merge rules for tasks and termination signals on the same node |
| `test_reporter_pushes_errors_via_push_errors_endpoint_only` | Error push endpoint unified as `/api/push_errors`, full push payload structure |
| `test_reporter_pushes_only_errors_after_server_max_event_id` | Incremental error push based on server watermark |

## How to Run

```bash
# Run all injection and push tests
pytest tests/observability/test_reporter.py -v

# Run injection payload parsing tests only
pytest tests/observability/test_reporter.py -k "accepts_split" -v

# Run merge rule tests only
pytest tests/observability/test_reporter.py -k "merges" -v

# Run error push tests only
pytest tests/observability/test_reporter.py -k "push_errors" -v
```

## Notes

- Tests use Fake objects to completely isolate network dependencies; `TaskReporter`'s actual HTTP behavior is verified in other tests.
- Task payloads and termination signals are already split at the remote end; the Reporter side is responsible for re-merging them and replacing termination signals with the `TERMINATION_SIGNAL` singleton.
- `FakePushSession` records the URL, JSON payload, and timeout of each POST, making it easy to assert push content without depending on a real network.
- The related implementation is located at `src/celestialflow/observability/core_report.py`.
