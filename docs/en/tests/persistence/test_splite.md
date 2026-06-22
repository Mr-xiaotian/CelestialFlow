# SQLite Utility Tests (test_splite.py)

> 📅 Last Updated: 2026/06/18

## Purpose

Validates all sqlite utility functions in the `celestialflow.persistence.util_sqlite` module, ensuring correct and reliable behavior for database table creation, record CRUD operations, state transitions, and stage-based aggregation.

## Core Test Objects

| Function | Description |
|------|------|
| `connect_db` | Establishes a connection and auto-creates the records table and indexes |
| `normalize_record` | Normalizes error records into sqlite-writable format |
| `insert_record` | Inserts a single record (skips metadata rows) |
| `load_records` | Reads all records filtered by status |
| `append_records` | Batch appends records (skips duplicate event_ids) |
| `query_records` | Paginated, filtered, and sorted queries |
| `clear_records` | Clears the records table |
| `get_max_event_id_in_fail` | Gets the maximum event_id for failed status only |
| `load_records_after_event_id_in_fail` | Incrementally reads records above a failed event_id lower bound |
| `load_records_grouped_by_stage` | Reads failed records grouped by stage |
| `promote_record_to_failed_by_event_id` | Updates status to failed and writes error information |
| `promote_record_to_success_by_event_id` | Updates status to success and writes result |
| `update_record_event_id_by_event_id` | Migrates a record's event_id |
| `delete_record_by_event_id` | Deletes a record by event_id |
| `load_task_error_records` | Reads task-error pairs by stage |
| `load_task_result_records` | Reads task-result pairs by stage |

## Test Coverage Matrix

| Test Class | Case Count | Coverage Target |
|--------|--------|---------|
| `TestSpliteUtils` | 14 | Connection & table creation, normalization, insert/read, append/dedup, paginated query, clear, incremental/grouped reads, state transitions, event_id migration, deletion, paired reads |

## Key Test Scenarios

### Table Creation and Indexes

- `connect_db` auto-creates the `records` table and `idx_records_event_id`, `idx_records_status_id` indexes
- Verifies the `result_json` field exists

### Normalization

- Metadata rows (no `ts`) return `None` and are not stored in the database
- Error records are normalized to `status="failed"`, with `task_json` and `result_json` serialized as JSON strings

### Insert and Read

- Metadata row inserts return `False` and are not written
- `load_records` can filter by `status`

### Append and Deduplication

- `append_records` skips existing `event_id`s, ensuring idempotent repeated synchronization

### Paginated Query

- `query_records` supports `page`/`page_size`/`node`/`keyword`/`sort_order` parameters
- Verifies sort order rules (newest/oldest) and filtering accuracy

### State Transitions

- `promote_record_to_failed_by_event_id`: from waiting to failed, updates event_id and error info
- `promote_record_to_success_by_event_id`: from pending to success, writes result
- `update_record_event_id_by_event_id`: retains current status, only migrates event_id

### Incremental and Grouped Reads

- `get_max_event_id_in_fail` only counts failed status
- `load_records_after_event_id_in_fail` reads incrementally by event_id lower bound
- `load_records_grouped_by_stage` only returns failed records, grouped by stage

### Paired Reads

- `load_task_error_records` returns a list of `(task_json, (error_type, error_message))`, supporting filtering by stage
- `load_task_result_records` returns a list of `(task_json, result_json)`

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

- Tests use the `tmp_path` fixture to create temporary sqlite files, automatically cleaned up after testing
- The `sample_errors` fixture provides 3 valid error records + 1 metadata row as the test dataset
- The related implementation is in `src/celestialflow/persistence/util_sqlite.py`
