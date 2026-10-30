# tests/persist/test_sqlite.py

> 📅 Last Updated: 2026/10/30

## Purpose

Validates the sqlite utility functions in `celestialflow.persist.util_sqlite`, ensuring that table and index creation, record normalization, single-record insertion, state transitions (failed / success), retry information updates, deletion by event_id, and per-node paired reads all behave correctly and reliably.

> This test file was renamed from the historical `test_splite.py`; the test class name `TestSpliteUtils` retains its historical spelling (should be `TestSqliteUtils`), kept as in the source code.

## Core Test Objects

All the functions under test come from `celestialflow.persist.util_sqlite`:

| Function | Description |
|------|------|
| `connect_db` | Establishes a connection (`check_same_thread=False`, WAL, `synchronous=NORMAL`), auto-creates the records table and indexes, and automatically adds `retry_times` when an old database is missing the column |
| `normalize_record` | Normalizes records into sqlite-writable format; metadata rows without `event_id` return `None`, and business records missing `node` or `status` raise `KeyError` |
| `insert_record` | Inserts a single record on an existing connection; metadata rows return `False`, and an actual insertion returns `True` |
| `row_to_record_dict` | Converts a `sqlite3.Row` into an outward-facing record dictionary, deserializing `task_json` / `result_json` into Python objects |
| `promote_record_to_failed_by_event_id` | Updates the status to failed, replaces `event_id` with the error event ID, and writes the error info and timestamp |
| `promote_record_to_success_by_event_id` | Updates the status to success, writes the result and timestamp, and retains the original `event_id` |
| `update_retry_by_event_id` | Updates the record's retry count and latest error info, keeping the status unchanged; returns `False` when the record does not exist |
| `delete_record_by_event_id` | Deletes a record by event_id |
| `load_task_error_records` | Reads a list of `(task_json, (error_type, error_message))` per node |
| `load_task_result_records` | Reads a list of `(task_json, result_json)` per node |

This file also defines two test helper functions (not objects under test):

| Helper | Description |
|----------|------|
| `_insert_records(sqlite_path, records)` | Writes records one by one with `connect_db` + `insert_record`, skipping `sqlite3.IntegrityError` (duplicate `event_id`) and returning the actual number written |
| `_fetch_records(sqlite_path, status)` | Queries by `status` with `connect_db` and converts rows into a list of dictionaries via `row_to_record_dict`, for assertion reads |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestSpliteUtils` | 11 | Connection, table and index creation, normalization, insert and read, failed / success state transitions, retry updates (including missing records), deletion by event_id, per-node paired reads |

## Key Test Scenarios

### Table and Index Creation

- `connect_db` auto-creates the `records` table, the `idx_records_event_id` (unique) index, and the `idx_records_status_id` index.
- Confirms via `PRAGMA index_list(records)` that `idx_records_event_id` is a unique index.
- Checks that the table structure field order is `id / event_id / ts / node / status / error_type / error_message / task_json / result_json / retry_times`, and confirms the `result_json` field exists.

### Normalization

- Metadata rows missing `event_id` (e.g., containing only `timestamp` / `graph_name`) make `normalize_record` return `None`.
- Business records missing `node` or `status` raise `KeyError`, matching the field name in the message.
- Valid records are normalized to fields such as `event_id` / `node` / `status` / `error_type` / `error_message` / `ts` / `retry_times`, with `retry_times` defaulting to 0 and `task_json` serialized as a JSON string.

### Insert and Read

- For a metadata row, `insert_record` returns `False` and nothing is written; for two valid records it returns `True`.
- When `_fetch_records` reads back via `row_to_record_dict`, `task_json` is deserialized into a Python object, `result_json` is `None`, and `id` auto-increments in insertion order.

### State Transitions

- `promote_record_to_failed_by_event_id`: migrates from the waiting record (`event_id=9`) to the new error event ID (19), writes `status="failed"`, `ts=9.5`, `error_type="RuntimeError"`, `error_message="boom"`, and returns `True`.
- `promote_record_to_success_by_event_id`: promotes the pending record (`event_id=8`) to success, retaining the original `event_id`, writing `ts=8.5` and `result_json`, with `task_json` unchanged.

### Retry Updates

- `update_retry_by_event_id`: writes `retry_times=2`, `ts`, `error_type` / `error_message` to a pending record; the status remains `pending` and it returns `True`.
- Updating a non-existent `event_id=999` returns `False`.

### Deletion

- `delete_record_by_event_id(conn, 2)` returns `True`, and the remaining failed records have `event_id` values `[1, 3]`.

### Paired Reads

- `load_task_error_records(db_path, "s1")` returns only s1's failed records, sorted by `id` ascending, with elements of the form `(task_json, (error_type, error_message))`.
- `load_task_result_records(db_path, "s8")` returns `[(task_json, result_json)]`.

## How to Run

```bash
# Run all
pytest tests/persist/test_sqlite.py -v

# Match by keyword
pytest tests/persist/test_sqlite.py -k "connect or normalize" -v
pytest tests/persist/test_sqlite.py -k "insert" -v
pytest tests/persist/test_sqlite.py -k "promote or retry" -v
pytest tests/persist/test_sqlite.py -k "delete" -v
pytest tests/persist/test_sqlite.py -k "load_task" -v
```

## Notes

- Tests use the `tmp_path` fixture to create temporary sqlite files, automatically cleaned up after testing.
- The `sample_errors` fixture provides 3 valid error records + 1 metadata row as the test dataset; the `sqlite_path` fixture provides the `tmp_path / "records.sqlite3"` path.
- All write operations are performed on the connection returned by `connect_db`, with the test itself calling `commit()` and `close()`.
- The node identifier field in the sqlite `records` table is `node`; all functions that read / filter per node use `node`.
- The related implementation is in `src/celestialflow/persist/util_sqlite.py`.
