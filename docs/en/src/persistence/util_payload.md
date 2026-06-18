# PersistencePayload

> 📅 Last Updated: 2026/06/18

`persistence/util_payload.py` provides a persistence serialization utility for task data, recursively converting arbitrary Python objects into JSON-friendly structures.

> ⚠️ **Changed**: This file replaces the old `util_jsonl.py`. The old version provided JSONL file read/write utilities, while the new module uses SQLite storage. This file focuses on data serialization; for SQLite operations, see `util_sqlite.py`.

## Core Function

### to_persisted_payload

```python
def to_persisted_payload(task: Any) -> Any:
    """
    Converts a task into a JSON-friendly persistable structure.

    :param task: Task data to be serialized
    :return: A JSON-friendly persistable structure
    """
```

**Conversion Rules:**

| Input Type | Output | Description |
|---------|------|------|
| `None` / `str` / `int` / `float` / `bool` | Returned as-is | Already JSON-native types |
| `list` / `tuple` / `set` | `list` | Recursively convert each element |
| `dict` | `dict` | Keys converted to `str`, values recursively converted |
| Other types | `str(task)` | Converted to string representation |

```mermaid
flowchart TD
    Input[Input task] --> CheckType{Type Check}
    CheckType -->|None / str / int / float / bool| Primitive[Return as-is]
    CheckType -->|list / tuple / set| Iterable[Convert to list<br/>Recursively convert each element]
    CheckType -->|dict| DictType[Keys to str<br/>Values recursively converted]
    CheckType -->|Other| Str[str task]
```

## Usage Example

### Primitive Types Pass Through Directly

```python
from celestialflow.persistence.util_payload import to_persisted_payload

print(to_persisted_payload(42))       # 42
print(to_persisted_payload("hello"))  # "hello"
print(to_persisted_payload(True))     # True
print(to_persisted_payload(None))     # None
```

### Compound Types Recursively Converted

```python
from celestialflow.persistence.util_payload import to_persisted_payload

# List
result = to_persisted_payload([1, "a", True])
print(result)  # [1, 'a', True]

# Nested dict
result = to_persisted_payload({"score": 95, "tags": ["a", "b"]})
print(result)  # {'score': 95, 'tags': ['a', 'b']}

# Custom object
class MyTask:
    def __str__(self):
        return "MyTask(id=1)"

result = to_persisted_payload(MyTask())
print(result)  # "MyTask(id=1)"
```

### Usage in FallbackInlet

`to_persisted_payload` is mainly called internally by `FallbackInlet` to convert task data into JSON strings storable in SQLite:

```python
# Internal flow of FallbackInlet.task_in:
pending_item = {
    "__op__": "insert",
    "record": {
        "event_id": event_id,
        "stage": stage_name,
        "status": "pending",
        "task_json": to_persisted_payload(task),  # Auto-serialized
    },
}
```

## Notes

- The serialization strategy is **best-effort**: for objects that cannot be directly JSON-serialized, it falls back to `str()` string representation.
- The function result is written to the `task_json` or `result_json` field of SQLite via `json.dumps` internally by `FallbackSpout`.
- Difference from the old `util_jsonl.py`: the new version no longer handles JSONL file I/O, focusing solely on data format conversion.
