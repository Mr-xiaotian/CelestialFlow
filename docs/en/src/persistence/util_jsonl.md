# PersistenceJSONL

> 📅 Last Updated: 2026/05/24

`persistence/util_jsonl.py` provides JSONL persistence and reading utilities.

## Reading Interface

| Function | Description |
|------|------|
| `load_jsonl_logs(path, start_seq=1, keys=None)` | Read line by line, optional field filtering, supports starting from a specified line number |
| `load_jsonl_by_key(jsonl_path, extract_key="stage", extract_value="task")` | Load grouped by a specified field, supports custom grouping key and extracted value field |
| `load_jsonl_grouped_by_keys(jsonl_path, group_keys, extract_field)` | Read grouped by multiple fields, supports field extraction and `ast.literal_eval` deserialization |
| `load_task_by_stage(jsonl_path)` | Load error records, categorized by stage, returns `{stage_name: [task_list]}` |
| `load_task_by_error(jsonl_path)` | Load error records, categorized by error_type and stage, returns `{(error_type, stage): [task_list]}` |
| `load_task_error_pairs(jsonl_path)` | Load error records, returns a list of `(task, PersistedErrorRecord)` pairs |

### Internal Functions

| Function | Description |
|------|------|
| `_parse_error_record(item)` | Parse a `PersistedErrorRecord` object from a JSONL record |
| `parse_jsonl_value(val)` | Smart parsing of JSONL field values, supports `ast.literal_eval` deserialization of string-form lists/tuples |

#### parse_jsonl_value Details

This function is used to intelligently parse raw JSONL field values into Python objects:

```python
from celestialflow.persistence.util_jsonl import parse_jsonl_value

# String-form list → tuple
parse_jsonl_value("[1, 2, 3]")       # → (1, 2, 3)
parse_jsonl_value("(a, b, c)")       # → ("a", "b", "c")

# Plain strings unchanged
parse_jsonl_value("hello")           # → "hello"

# Already a list/tuple, directly converted
parse_jsonl_value([1, 2, 3])         # → (1, 2, 3)
parse_jsonl_value((1, 2, 3))         # → (1, 2, 3)
```

## Data Flow

```mermaid
flowchart LR
    JSONL[JSONL File] -->|json.loads| Row[Single Row Record]
    Row --> parse_jsonl_value
    parse_jsonl_value -->|ast.literal_eval| Parsed[Parsed Value]
    Row --> load_jsonl_logs[load_jsonl_logs]
    Row --> load_task_error_pairs[load_task_error_pairs]
```
