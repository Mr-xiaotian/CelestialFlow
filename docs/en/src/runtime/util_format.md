# RuntimeFormat

> 📅 Last Updated: 2026/08/12

`runtime/util_format.py` provides general formatting utility functions, including string truncation, table rendering, time formatting, etc.

> Note: The current file path is `src/celestialflow/runtime/util_format.py`; the legacy path `src/celestialflow/utils/util_format.py` is deprecated.

## Main Functions

| Function | Description |
|------|------|
| `format_repr(obj, max_length)` | Safely truncates object string representations, automatically escaping newlines and backslashes |
| `format_table(data, ...)` | Renders 2D data as a text table, supporting `left` / `right` / `center` alignment |
| `format_duration(seconds)` | Converts seconds to a readable duration (`MM:SS` or `HH:MM:SS`) |
| `format_timestamp(timestamp)` | Converts a timestamp to a `YYYY-MM-DD HH:MM:SS` formatted string |
| `cluster_by_value_sorted(input_dict)` | Clusters by value, sorts results by value in ascending order |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

Formats an object as a string, automatically escaping newlines and backslashes, and truncating with the `first 2/3 + ... + last 1/3` pattern when too long.

## format_table

```python
def format_table(
    data: list[Any],
    row_names: list[Any] | None = None,
    column_names: list[str] | None = None,
    index_header: str = "#",
    fill_value: str = "N/A",
    align: str = "left",
) -> str: ...
```

Formats 2D data as a bordered text table. Supports automatic generation of Excel-style column names (A, B, ..., Z, AA, AB...).

## format_duration

```python
def format_duration(seconds: int) -> str: ...
```

Formats seconds as `HH:MM:SS` or `MM:SS`, automatically omitting the leading zeros when the hours component is 0.

## format_timestamp

```python
def format_timestamp(timestamp: float) -> str: ...
```

Formats a timestamp (in seconds) as `YYYY-MM-DD HH:MM:SS`.

## cluster_by_value_sorted

```python
def cluster_by_value_sorted(input_dict: dict[str, int]) -> dict[int, list[str]]: ...
```

Clusters by value, with results sorted by value (integer key) in ascending order. Used by `TaskGraph._build_analysis()` to build hierarchical dictionaries.

## Usage Examples

```python
from celestialflow.runtime.util_format import (
    format_repr,
    format_table,
    format_duration,
    format_timestamp,
)

# format_repr: safe truncation
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC

# format_duration: time formatting
print(format_duration(59))  # 00:59
print(format_duration(3661))  # 01:01:01

# format_timestamp: timestamp formatting
print(format_timestamp(0))  # 1970-01-01 08:00:00

# format_table: table rendering
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
]
table = format_table(
    data=data,
    column_names=["Mode", "Task Count", "Time (s)"],
)
print(table)
```

## cluster_by_value_sorted Example

```python
from celestialflow.runtime.util_format import cluster_by_value_sorted

input_dict = {"A": 2, "B": 0, "C": 2, "D": 1}
result = cluster_by_value_sorted(input_dict)
print(result)  # {0: ['B'], 1: ['D'], 2: ['A', 'C']}
```
