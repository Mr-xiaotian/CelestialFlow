# tests/reporter/test_push.py

> 📅 Last Updated: 2026/11/13

## Purpose

Verifies the push pipeline of `celestialflow.reporter.core_push`:

- `PushInlet.on_event(event)` uses `match` to map `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` to `PushRecord`s of the corresponding `kind`, enqueued via `send()`;
- `PushSpout` POSTs records to different endpoints according to the record type, raising `ReporterError` on non-2xx responses;
- The background thread consumes the queue, a single failure does not kill the thread, and `stop()` closes the HTTP session;
- `NullPushSpout` does not create an HTTP session and simply discards records.

## Core Test Objects

| Object | Source | Description |
|------|------|------|
| `PushInlet` | `celestialflow.reporter` | Observer entry point `on_event()` + enqueue method `send()`; also includes `push_snapshot()` |
| `PushSpout` | `celestialflow.reporter` | Push spout, the consumer of the `PushRecord` queue |
| `NullPushSpout` | `celestialflow.reporter` | No-op spout implementation |
| `PushRecord` | `celestialflow.reporter.core_push` | Frozen dataclass that reuses different fields according to `kind` |
| `GraphStartEvent` / `GraphEndEvent` / `TaskFailEvent` | `celestialflow.observer` | The three event types mapped on enqueue |
| `ReporterError` | `celestialflow.runtime.util_errors` | Expected exception for non-2xx responses |
| `wait_until` | `tests/conftest.py` | Polls until the background thread finishes consuming (default 5-second timeout) |

## Key Fixtures and Fakes

| Name | Purpose |
|------|------|
| `FakePostResponse` | Simulated response with configurable `ok` and `status_code` |
| `FakePushSession` | A `requests.Session` stand-in: `post()` records `(url, json, timeout)`; `close()` sets `closed = True` |
| `_fail_event(...)` | Builds `TaskFailEvent(node, task, f"({task})", exception, task_id=1, error_id)`, defaulting to `error_id=21`, `node="s1"`, `task="data1"`, `ValueError("oops")` |
| `_start_event()` | Builds a `GraphStartEvent` carrying graph metadata (`g1` / `thread` / `is_dag=True` / two nodes and `node_meta`) |
| `_end_event()` | Builds `GraphEndEvent(graph="g1", end_time=456.0, elapsed=1.5)` |
| `_dequeue(spout)` | Takes one record from `spout.get_queue()` and asserts its type is `PushRecord` |

## Test Coverage Matrix

| Case | Coverage Target |
|------|---------|
| `test_inlet_maps_task_fail_event` | Failure event → `kind="task_fail"`, `event_id` / `node` / `task_json` / `error_type` / `error_message` / `ts` |
| `test_inlet_maps_graph_start_event` | Graph start event → `kind="graph_start"`, with all graph metadata fields passed through |
| `test_inlet_maps_graph_end_event` | Graph end event → `kind="graph_end"`, `end_time` / `elapsed` |
| `test_spout_pushes_task_fail_to_push_error_endpoint` | `POST /api/push_error` and the payload fields |
| `test_spout_pushes_graph_start_to_graph_meta_endpoint` | `POST /api/push_graph_meta` and the top-level graph metadata fields |
| `test_spout_pushes_graph_end_to_shutdown_endpoint` | `POST /api/shutdown_session`, payload only `session_id` |
| `test_handle_record_raises_reporter_error_on_failure` | On non-2xx, `_handle_record` raises `ReporterError` |
| `test_spout_thread_drains_records_and_closes_session` | The background thread consumes two records, the queue is emptied, and the session is closed after `stop()` |
| `test_spout_thread_survives_push_failure` | Continuous failures do not kill the thread, records are still consumed, and the thread can be stopped normally |
| `test_null_spout_discards_records` | `NullPushSpout` does not create a session and records are drained |

## Key Behavior Details

### Event → Record Mapping

| Event | `PushRecord.kind` | Fields Used |
|------|-------------------|---------|
| `GraphStartEvent` | `"graph_start"` | `graph`, `graph_mode`, `start_time`, `is_dag`, `nodes`, `edges`, `source_nodes`, `node_meta` |
| `GraphEndEvent` | `"graph_end"` | `graph`, `end_time`, `elapsed` |
| `TaskFailEvent` | `"task_fail"` | `event_id ← error_id`, `node`, `task_json ← to_persisted_payload(task)`, `error_type ← exception type name`, `error_message ← str(exception)`, `ts ← time.time()` |
| Other events | Not enqueued | `case _: pass` in the `match` |

- `PushInlet` inherits both `BaseInlet` and `Observer`; the event entry point is uniformly `on_event(event)`, and records are always enqueued via `send()` (provided by `BaseInlet`, which writes to the bound spout's queue).
- `task_json` goes through `to_persisted_payload`, so in the test `task={"value": 1}` yields a structurally identical dictionary; non-serializable objects are projected into a persistable form.
- The field name of `error_id` in the record is `event_id`.

### Record → Endpoint

| `kind` | Endpoint | Payload Highlights |
|--------|------|---------|
| `graph_start` | `{base_url}/api/push_graph_meta` | `session_id` + all graph metadata fields (flattened at the top level) |
| `graph_end` | `{base_url}/api/shutdown_session` | Only `{"session_id": ...}`; `end_time` / `elapsed` are **not sent** |
| `task_fail` | `{base_url}/api/push_error` | `session_id`, `event_id`, `node`, `task_json`, `error_type`, `error_message`, `ts` |
| `snapshot` | `{base_url}/api/push_snapshot` | See `test_snapshot.md` |

- Assertions about fields such as `payload["timestamp"]` are outside the scope of this file; this file only covers the three event record types above.
- The semantics of `graph_end` are "session offline notification": after receiving it, the server marks the session as ended, while the session data and error database are retained.
- Every POST carries `timeout=self.timeout` (constructor default `3.0`); the tests only unpack it as `_timeout` without rewriting the assertions.

### Background Thread and Failure Isolation

- `PushSpout.start()` creates the `requests.Session` through `BaseSpout._before_start()` and then starts a daemon thread that loops over `get_queue()`.
- `ReporterError` raised by `_handle_record` is caught by the `try/except Exception` in `BaseSpout._spout` and printed, and the thread keeps consuming; `get_pending_count()` is decremented in `finally`.
- `stop()` puts a termination signal into the queue and `join`s (at most 5 seconds); after the thread exits, `_after_stop()` closes the session.
- Thread cases inject a fake session via `monkeypatch.setattr(push_module.requests, "Session", lambda: session)` and wait for consumption to finish with `wait_until(lambda: len(session.posts) == 2 and spout.get_pending_count() == 0)`.
- `test_spout_thread_survives_push_failure` uses a session with `ok=False`, waits only for `get_pending_count() == 0`, and finally asserts `session.closed`, proving that failures do not block stopping.

### The Null Variant

`NullPushSpout` overrides `_handle_record` to discard records directly and does not override `_before_start`, so it never creates a `requests.Session`. The test replaces `requests.Session` with `pytest.fail(...)`, which fails immediately if it is called; it then starts, enqueues two records, waits for the queue to drain, and stops.

## How to Run

```bash
# Run all
uv run pytest tests/reporter/test_push.py -v

# Enqueue mapping only
uv run pytest tests/reporter/test_push.py -k "inlet_maps" -v

# Endpoint pushing only
uv run pytest tests/reporter/test_push.py -k "endpoint" -v

# Background thread only
uv run pytest tests/reporter/test_push.py -k "thread or null" -v
```

## Notes

- Non-thread cases assign a fake session directly to `spout._session` to bypass `start()`; this relies on the private field name `_session` of the implementation under test, so renaming it requires updating the test accordingly.
- Thread cases rely on `wait_until` from `tests/conftest.py` (imported via the root `conftest`), with a default timeout of 5 seconds; the actual duration should be far below that.
- Records that were enqueued but not consumed may remain in the queue; tests take them out synchronously via `spout.get_queue().get()` without starting the thread.
- The related implementation is in `src/celestialflow/reporter/core_push.py`; for the semantics, see `docs/zh-CN/src/reporter/core_push.md`.
