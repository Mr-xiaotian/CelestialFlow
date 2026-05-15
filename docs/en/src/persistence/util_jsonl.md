# PersistenceJSONL

> 📅 Last Updated: 2026/05/15

`persistence/util_jsonl.py` provides JSONL persistence and reading utilities.

## Reading Interface

- `load_jsonl_logs`: Reads line by line with optional field filtering, supports starting from a specified line number.
- `load_jsonl_grouped_by_keys`: Reads grouped by multiple fields, supports field extraction and `ast.literal_eval` deserialization.
- `load_task_by_stage`: Loads error records, categorized by stage.
- `load_task_by_error`: Loads error records, categorized by error and stage.
- `load_jsonl_by_key`: Loads values from a JSONL file grouped by a specified field, supports custom grouping keys and value extraction fields.
- `load_task_error_pairs`: Loads error records, returning a list of `(task, error)` pairs.
