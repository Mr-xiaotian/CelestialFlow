# src/celestialflow/persist/util_sqlite.py

> 📅 Last Updated: 2026/10/09

`persist/util_sqlite.py` provides SQLite database connection management and record CRUD operation utilities, serving as the underlying storage engine for `LifecycleSpout`.

## Core Function Overview

| Function | Description |
|------|------|
| `connect_db(db_path)` | Creates a SQLite connection, configures WAL mode, and ensures the table structure and indexes |
| `normalize_record(record)` | Normalizes a record into a sqlite-writable format (returns `None` when `event_id` is missing) |
| `row_to_record_dict(row)` | Converts a sqlite row into an outward-facing record dictionary |
| `insert_record(conn, record)` | Inserts a record |
| `promote_record_to_success_by_event_id(...)` | Promotes a record to success and writes the result |
| `promote_record_to_skipped_by_event_id(...)` | Promotes a record to skipped and switches to a new event ID |
| `promote_record_to_failed_by_event_id(...)` | Promotes a record to failed and switches to a new event ID |
| `update_retry_by_event_id(conn, event_id, *, ts, retry_times, ...)` | Updates the retry count and most recent error info of a pending record |
| `delete_record_by_event_id(conn, event_id)` | Deletes a record by event_id |
| `clear_records(db_path)` | Clears all records in the database |
| `append_records(db_path, records)` | Batch append writes; skips on event_id conflict (idempotent) |
| `get_max_event_id_in_fail(db_path)` | Reads the maximum event_id among failure records |
| `load_records(db_path, status)` | Loads records by status |
| `load_tasks_grouped_by_node(db_path, statuses)` | Loads records grouped by node |
| `load_records_after_event_id_in_fail(db_path, min_event_id)` | Incrementally loads failure records |
| `query_records(db_path, page, page_size, ...)` | Paginated conditional query |
| `query_error_type_counts(db_path, node, status)` | Aggregated counts by error type |
| `load_task_error_records(db_path, node)` | Loads (task, error) pairs by node |
| `load_task_result_records(db_path, node)` | Loads (task, result) pairs by node |

## Database Table Structure

```sql
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ts REAL,
    node TEXT NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    task_json TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT 'null',
    retry_times INTEGER NOT NULL DEFAULT 0
)
```

> Backward compatibility with old databases: `_ensure_table` checks the `retry_times` column and automatically runs `ALTER TABLE` to add it if missing.

**Indexes:**
- `idx_records_event_id` (UNIQUE): Fast lookup by event_id
- `idx_records_status_id`: Composite query by (status, id)

> The `node` field in the table identifies the node to which a task belongs (a business field that must be explicitly written by the caller).

## Connection Management

### connect_db

```python
def connect_db(db_path: str | Path) -> sqlite3.Connection:
```

Automatic configuration:
- `check_same_thread=False` — Multi-thread safety
- `journal_mode=WAL` — Write operations do not block reads
- `synchronous=NORMAL` — Balances performance and safety
- `foreign_keys=ON` — Enables foreign key constraints

At the same time it ensures the table structure and indexes exist.

## Record Serialization

### normalize_record

```python
def normalize_record(record: dict[str, Any]) -> dict[str, Any] | None:
```

- Returns `None` when `event_id` is missing (non-business records are ignored).
- Business records must explicitly provide `node` and `status`.
- The output is a standard parameter dictionary: `event_id` / `node` / `status` / `error_type` / `error_message` / `ts` / `task_json` / `result_json` / `retry_times`, where `task_json` / `result_json` are the result of `json.dumps(..., ensure_ascii=False)`.

### row_to_record_dict

Converts a sqlite row (`sqlite3.Row`) into an outward-facing record dictionary, where `task_json` / `result_json` are restored via `json.loads`.

## Record Operations

### Write Operations (requires passing `conn`)

The following functions require the caller to manage the `conn` lifecycle (typically held by `LifecycleSpout`), and to manually `commit()` after modifying a record:

| Function | Signature Highlights | Description |
|------|---------|------|
| `insert_record` | `(conn, record: dict) -> bool` | Normalizes and INSERTs |
| `update_retry_by_event_id` | `(conn, event_id, *, ts, retry_times, error_type="", error_message="") -> bool` | Keeps the pending state, updates the retry count and the most recent error info |
| `promote_record_to_success_by_event_id` | `(conn, event_id, result, *, ts) -> bool` | Updates status='success' + result_json |
| `promote_record_to_skipped_by_event_id` | `(conn, event_id, new_event_id, *, ts) -> bool` | Updates event_id, status='skipped' |
| `promote_record_to_failed_by_event_id` | `(conn, event_id, new_event_id, *, ts, error_type="", error_message="") -> bool` | Updates event_id, status='failed', and error info |
| `delete_record_by_event_id` | `(conn, event_id) -> bool` | Deletes a record |

### Self-managed Connection Operations

The following functions call `connect_db` and `close` internally:

| Function | Signature Highlights | Return Type |
|------|---------|---------|
| `clear_records` | `(db_path)` | `None` |
| `append_records` | `(db_path, records)` | `int` (number actually inserted) |
| `get_max_event_id_in_fail` | `(db_path)` | `int | None` |
| `load_records` | `(db_path, status="failed")` | `list[dict]` |
| `load_tasks_grouped_by_node` | `(db_path, statuses=("failed", "pending"))` | `dict[str, list[dict]]` |
| `load_records_after_event_id_in_fail` | `(db_path, min_event_id)` | `list[dict]` |
| `query_records` | `(db_path, page, page_size, node, keyword, sort_order, status="failed")` | `(total, total_pages, items)` |
| `query_error_type_counts` | `(db_path, node="", status="failed")` | `list[dict]` |
| `load_task_error_records` | `(db_path, node)` | `list[(task, (error_type, error_message))]` |
| `load_task_result_records` | `(db_path, node)` | `list[(task, result)]` |

## Usage Examples

### Basic Read/Write Operations

```python
import sqlite3
from celestialflow.persist.util_sqlite import connect_db, insert_record, load_records

# 1. Create a connection (auto-configuration + table creation)
conn = connect_db("test_data.sqlite3")

# 2. Write a record (requires passing conn)
record = {
    "event_id": 1,
    "node": "StageA",
    "status": "pending",
    "task_json": "hello world",
}
insert_record(conn, record)
conn.commit()
conn.close()

# 3. Read records (auto-managed connection)
records = load_records("test_data.sqlite3", status="pending")
for r in records:
    print(f"event_id={r['event_id']}, node={r['node']}, task={r['task_json']}")
```

### Load Grouped by Node

```python
from celestialflow.persist.util_sqlite import load_tasks_grouped_by_node

grouped = load_tasks_grouped_by_node(
    "lifecycles/2026-10-09/flow_lifecycle(10-00-00-123).sqlite3",
    ("failed", "pending"),
)
```

Returns `{node_name: [{"task_json": task, "error_type": str, "status": str}, ...]}`.

### Paginated Error Record Query

```python
from celestialflow.persist.util_sqlite import query_records

total, total_pages, items = query_records(
    db_path="lifecycles/2026-10-09/flow_lifecycle(10-00-00-123).sqlite3",
    page=1,
    page_size=20,
    node="",
    keyword="ValueError",
    sort_order="newest",
    status="failed",
)
print(f"Total {total} records, page 1/{total_pages}")
```

### Reading Task Error / Result Pairs

```python
from celestialflow.persist.util_sqlite import (
    load_task_error_records,
    load_task_result_records,
)

errors = load_task_error_records(
    db_path, node="StageA"
)  # [(task, (error_type, error_message))]
results = load_task_result_records(db_path, node="StageA")  # [(task, result)]
```

## Notes

- **Write functions** (insert/promote/delete) require the caller to pass `conn` and manually `commit()` after operations; `clear_records` / `append_records` and all read functions manage connections internally.
- `insert_record` uses `INSERT`, guaranteeing uniqueness based on the `event_id` unique index; external batch writes usually cooperate with `append_records` to capture `IntegrityError` and achieve idempotency.
- The normalization function `normalize_record` filters out records missing `event_id` (returns `None`).
- `task_json` and `result_json` store `json.dumps`-serialized strings; they are restored via `json.loads` upon reading.
- `retry_times` is maintained by `update_retry_by_event_id`, recording the number of retries before a task is promoted.
- **Business fields are explicitly written**: `node` and `status` are business fields that must be explicitly provided by the caller (such as `LifecycleInlet`) when writing a record; `normalize_record` does not make default inferences.