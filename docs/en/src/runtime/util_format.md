# src/celestialflow/runtime/util_format.py

> 📅 Last Updated: 2026/10/30

`runtime/util_format.py` provides general formatting utility functions, including string truncation, table rendering, and clustering by value.

## Main Functions

| Function | Description |
|----------|-------------|
| `format_repr(obj, max_length)` | Safely truncates object string representations, automatically escaping newlines and backslashes |
| `format_table(data, ...)` | Renders 2D data as a text table, supporting `left` / `right` / `center` alignment |
| `cluster_by_value_sorted(input_dict)` | Clusters by value, sorts results by value in ascending order |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

Formats an object as a string, automatically escaping newlines and backslashes, and truncating with the `first 2/3 + ... + last 1/3` pattern when too long:

- First does `str(obj)`, then doubles backslashes (`\` → `\\`) and replaces newlines with the two characters `\` + `n`
- When `max_length <= 0` or the length is within the limit, returns the string as-is (no truncation)
- When truncating, `segment_len = max(1, max_length // 3)`, taking the first `2 * segment_len` characters + `...` + the last `segment_len` characters

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

- Returns the string `"表格数据为空！"` when `data` is empty
- When `column_names` is omitted or too short, names are auto-filled in Excel style; when `row_names` is omitted, `0..n-1` is used as the row index
- When row lengths differ, `fill_value` is used for padding
- `align` supports `"left"` / `"right"` / `"center"`; unknown values fall back to left alignment

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
)

# format_repr: safe truncation
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...AAAAAAAAAA (20 + 3 + 10)
print(format_repr("a\nb", 50))  # a\nb (the newline is escaped to a literal \n)
print(format_repr("A" * 100, 0))  # no truncation, returns all 100 A's

# format_table: table rendering
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
]
table = format_table(
    data=data,
    column_names=["Mode", "Task Count", "Elapsed (s)"],
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
