# PersistenceSQLite

> 📅 Last Updated: 2026/06/22

`persistence/util_sqlite.py` provides SQLite database connection management and record CRUD operation utilities, serving as the underlying storage engine for `FallbackSpout` and `TaskReporter`.

## Core Function Overview

| Function | Description |
|----------|-------------|
| `connect_db(db_path)` | Creates a SQLite connection, configures WAL mode, and ensures table structure |
| `insert_record(conn, record)` | Inserts a record |
| `promote_record_to_failed_by_event_id(...)` | Promotes a pending record to failed |
| `promote_record_to_success_by_event_id(...)` | Promotes a pending record to success |
| `update_record_event_id_by_event_id(...)` | Updates a record's event_id |
| `delete_record_by_event_id(conn, event_id)` | Deletes a record by event_id |
| `load_records(db_path, status)` | Loads records by status |
| `load_records_grouped_by_stage(db_path, status)` | Loads records grouped by stage |
| `load_records_after_event_id_in_fail(db_path, min_event_id)` | Incrementally loads failed records |
| `query_records(db_path, page, page_size, ...)` | Paginated conditional query |
| `load_task_error_records(db_path, stage)` | Loads (task, error) pairs by stage |
| `load_task_result_records(db_path, stage)` | Loads (task, result) pairs by stage |

## Database Table Structure

```sql
CREATE TABLE IF NOT EXISTS records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    ts REAL,
    stage TEXT NOT NULL,
    status TEXT NOT NULL,
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    task_json TEXT NOT NULL,
    result_json TEXT NOT NULL DEFAULT 'null'
)
```

**Indexes:**
- `idx_records_event_id` (UNIQUE): Fast lookup by event_id
- `idx_records_status_id`: Composite query by (status, id)

## Connection Management

### connect_db

```python
def connect_db(db_path: str | Path) -> sqlite3.Connection:
    """
    Creates a sqlite connection and delegates lifecycle management to the caller.

    :param db_path: Path to the sqlite database file
    :return: A sqlite connection usable for record I/O
    """
```

Automatic configuration:
- `check_same_thread=False` — Multi-thread safety
- `journal_mode=WAL` — Write operations do not block reads
- `synchronous=NORMAL` — Balances performance and safety
- `foreign_keys=ON` — Enables foreign key constraints

## Record Operations

### Write Operations (requires passing `conn`)

The following functions require the caller to manage the `conn` lifecycle (typically held by `FallbackSpout`):

| Function | Signature Highlights | Description |
|----------|----------------------|-------------|
| `insert_record` | `(conn, record: dict) -> bool` | Normalizes and INSERTs |
| `promote_record_to_failed_by_event_id` | `(conn, event_id, new_event_id, *, ts, error_type="", error_message="") -> bool` | Updates event_id, status='failed', and error info |
| `promote_record_to_success_by_event_id` | `(conn, event_id, result, *, ts) -> bool` | Updates status='success' + result_json |
| `update_record_event_id_by_event_id` | `(conn, old_event_id, new_event_id, *, ts) -> bool` | Updates event_id (for retries) |
| `delete_record_by_event_id` | `(conn, event_id) -> bool` | Deletes a record |

### Read Operations (self-managed connection)

The following functions internally manage `connect_db` and `close` on their own:

| Function | Signature Highlights | Return Type |
|----------|----------------------|-------------|
| `load_records` | `(db_path, status="failed")` | `list[dict]` |
| `load_records_grouped_by_stage` | `(db_path, status="failed")` | `dict[str, list[dict]]` |
| `load_records_after_event_id_in_fail` | `(db_path, min_event_id)` | `list[dict]` |
| `query_records` | `(db_path, page, page_size, node, keyword, sort_order, status)` | `(total, total_pages, items)` |
| `load_task_error_records` | `(db_path, stage)` | `list[(task, (error_type, error_message))]` |
| `load_task_result_records` | `(db_path, stage)` | `list[(task, result)]` |

## Usage Examples

### Basic Read/Write Operations

```python
import sqlite3
from pathlib import Path
from celestialflow.persistence.util_sqlite import (
    connect_db,
    insert_record,
    load_records,
    delete_record_by_event_id,
)

# 1. Create connection
conn = connect_db("test_data.sqlite3")

# 2. Write record
record = {
    "event_id": 1,
    "stage": "StageA",
    "status": "pending",
    "task_json": "hello world",
}
insert_record(conn, record)
conn.commit()
conn.close()

# 3. Read records (auto-managed connection)
records = load_records("test_data.sqlite3", status="pending")
for r in records:
    print(f"event_id={r['event_id']}, task={r['task_json']}")

# 4. Clean up
Path("test_data.sqlite3").unlink()
```

### Recovering Failed Tasks from TaskExecutor

`TaskExecutor.start_db()` internally calls `load_records_grouped_by_stage`:

```python
from celestialflow.persistence.util_sqlite import load_records_grouped_by_stage

grouped = load_records_grouped_by_stage("fallback/2026-06-18/errors.sqlite3", "failed")
# {'StageA': [{'event_id': 1, 'task_json': 'hello', ...}, ...],
#  'StageB': [{'event_id': 2, 'task_json': 'world', ...}]}
```

### Paginated Error Record Query

```python
from celestialflow.persistence.util_sqlite import query_records

total, total_pages, items = query_records(
    db_path="fallback/2026-06-18/errors.sqlite3",
    page=1,
    page_size=20,
    node="",
    keyword="ValueError",
    sort_order="newest",
    status="failed",
)
print(f"Total {total} records, page 1/{total_pages}")
for item in items:
    print(f"  [{item['event_id']}] {item['error_type']}: {item['error_message']}")
```

## Notes

- **Write functions** (insert/promote/update/delete) require the caller to pass `conn` and manually `commit()` after operations.
- **Read functions** (load/query) internally manage the connection lifecycle; callers don't need to worry about connections.
- `insert_record` uses `INSERT`, guaranteeing uniqueness based on the `event_id` unique index; external batch writes usually cooperate with `append_records` to capture `IntegrityError` and achieve idempotency.
- The normalization function `normalize_record` filters out records missing `event_id` (returns `None`).
- `task_json` and `result_json` store `json.dumps`-serialized strings; they are restored via `json.loads` upon reading.
