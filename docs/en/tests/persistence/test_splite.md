# SQLite Utility Tests (test_splite.py)

> 📅 Last Updated: 2026/09/09

## Purpose

Validates all sqlite utility functions in the `celestialflow.persistence.util_sqlite` module, ensuring correct and reliable behavior for database table creation, record CRUD operations, state transitions, and stage-based aggregation.

## Core Test Objects

| Function | Description |
|------|------|
| `connect_db` | Establishes a connection and auto-creates the records table and indexes |
| `normalize_record` | Normalizes error records into sqlite-writable format; raises `KeyError` when `stage` or `status` is missing |
| `insert_record` | Inserts a single record (ignores metadata rows, returns `False`) |
| `load_records` | Reads all records filtered by status, with optional `status` parameter |
| `append_records` | Batch appends records (skips duplicate event_ids, returns the actual number of records written) |
| `query_records` | Paginated, filtered, and sorted queries (`page` / `page_size` / `node` / `keyword` / `sort_order`) |
| `query_error_type_counts` | Aggregates failed record counts by error type, with optional `node` filtering |
| `clear_records` | Clears the records table |
| `get_max_event_id_in_fail` | Gets the maximum event_id for failed status only; returns `None` when no record exists |
| `load_records_after_event_id_in_fail` | Incrementally reads records above a failed event_id lower bound |
| `promote_record_to_failed_by_event_id` | Updates status to failed and writes error information (`event_id` is replaced by the error event ID) |
| `promote_record_to_success_by_event_id` | Updates status to success and writes result |
| `delete_record_by_event_id` | Deletes a record by event_id |
| `load_task_error_records` | Reads a list of `(task_json, (error_type, error_message))` filtered by stage |
| `load_task_result_records` | Reads a list of `(task_json, result_json)` filtered by stage |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestSpliteUtils` | 17 | Connection & table creation, normalization, insert/read, append/dedup, paginated query, clear, incremental and grouped reads, error type aggregation, state transitions, deletion, paired reads |

## Key Test Scenarios

### Table Creation and Indexes

- `connect_db` auto-creates the `records` table and `idx_records_event_id`, `idx_records_status_id` indexes.
- Verifies that the `result_json` field exists, and checks the table structure field order is `id / event_id / ts / stage / status / error_type / error_message / task_json / result_json`.

### Normalization

- Metadata rows missing `event_id` (e.g., containing only `timestamp` / `graph_name`) return `None` and are not stored in the database.
- Business records missing `stage` or `status` cause `normalize_record` to raise `KeyError`.
- Error records are normalized to `status="failed"`, with `task_json` serialized as a JSON string.

### Insert and Read

- Metadata row `insert_record` returns `False` and is not written.
- `load_records` can filter by `status` (e.g., `"failed"` / `"success"`).
- `load_records` deserializes the `task_json` / `result_json` fields back into Python objects on read.

### Append and Deduplication

- `append_records` skips existing `event_id`s, ensuring idempotent repeated synchronization.
- The return value is the actual number of records written.

### Paginated Query

- `query_records` supports `page` / `page_size` / `node` / `keyword` / `sort_order` parameters.
- Verifies `newest` / `oldest` sorting and `keyword` fuzzy matching.
- Returns the tuple `(total, total_pages, page_items)`.

### Error Type Aggregation

- `query_error_type_counts` aggregates the counts of all failed records by error type (`error_type`), sorted by `count` in descending order.
- `query_error_type_counts` supports filtering by stage via the `node` parameter.
- Only counts records with status `failed`, ignoring other statuses such as success.

### State Transitions

- `promote_record_to_failed_by_event_id`: from waiting to failed, migrates event_id to the new error event ID and writes error info.
- `promote_record_to_success_by_event_id`: from pending to success, writes result and retains the original event_id.

### Incremental and Grouped Reads

- `get_max_event_id_in_fail` only counts failed status; returns `None` when there are no failed records.
- `load_records_after_event_id_in_fail` reads incrementally by event_id lower bound.
- `load_task_error_records` supports filtering by stage, returning a list of `(task_json, (error_type, error_message))`.

### Paired Reads

- `load_task_error_records` returns a list of `(task_json, (error_type, error_message))`, supporting filtering by stage.
- `load_task_result_records` returns a list of `(task_json, result_json)`.

## How to Run

```bash
# Run all
pytest tests/persistence/test_splite.py -v

# Match by keyword
pytest tests/persistence/test_splite.py -k "connect or normalize" -v
pytest tests/persistence/test_splite.py -k "insert or append" -v
pytest tests/persistence/test_splite.py -k "promote" -v
pytest tests/persistence/test_splite.py -k "group" -v
pytest tests/persistence/test_splite.py -k "load_task" -v
```

## Notes

- Tests use the `tmp_path` fixture to create temporary sqlite files, automatically cleaned up after testing.
- The `sample_errors` fixture provides 3 valid error records + 1 metadata row as the test dataset; the `sqlite_path` fixture provides the `tmp_path / "records.sqlite3"` path.
- The source filename `test_splite.py` is a historical spelling artifact (intended to be `splitter`); renaming is out of scope for this documentation task.
- The related implementation is in `src/celestialflow/persistence/util_sqlite.py`.
