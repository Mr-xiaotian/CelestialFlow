# RuntimeFormat

> 📅 最后更新日期: 2026/08/12

`runtime/util_format.py` 提供通用格式化工具函数，包括字符串截断、表格渲染、时间格式化等功能。

> 注意：当前文件路径为 `src/celestialflow/runtime/util_format.py`，旧路径 `src/celestialflow/utils/util_format.py` 已废弃。

## 主要函数

| 函数 | 说明 |
|------|------|
| `format_repr(obj, max_length)` | 安全截断对象字符串，自动转义换行和反斜杠 |
| `format_table(data, ...)` | 将二维数据渲染为文本表格，支持 `left` / `right` / `center` 对齐 |
| `format_duration(seconds)` | 秒数转可读时长（`MM:SS` 或 `HH:MM:SS`） |
| `format_timestamp(timestamp)` | 时间戳转 `YYYY-MM-DD HH:MM:SS` 格式字符串 |
| `cluster_by_value_sorted(input_dict)` | 按值聚类，按 value 升序排序 |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

将对象格式化为字符串，自动转义换行符和反斜杠，超长时按 `前 2/3 + ... + 后 1/3` 截断。

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

格式化二维数据为带边框的文本表格。支持自动生成 Excel 风格列名（A, B, ..., Z, AA, AB...）。

## format_duration

```python
def format_duration(seconds: int) -> str: ...
```

将秒数格式化为 `HH:MM:SS` 或 `MM:SS`，小时为 0 时自动省略前导零。

## format_timestamp

```python
def format_timestamp(timestamp: float) -> str: ...
```

将时间戳（秒）格式化为 `YYYY-MM-DD HH:MM:SS`。

## cluster_by_value_sorted

```python
def cluster_by_value_sorted(input_dict: dict[str, int]) -> dict[int, list[str]]: ...
```

按值聚类，结果按 value（整数键）升序排序。被 `TaskGraph._build_analysis()` 用于构建层级字典。

## 使用示例

```python
from celestialflow.runtime.util_format import (
    format_repr,
    format_table,
    format_duration,
    format_timestamp,
)

# format_repr：安全截断
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC

# format_duration：时间格式化
print(format_duration(59))    # 00:59
print(format_duration(3661))  # 01:01:01

# format_timestamp：时间戳格式化
print(format_timestamp(0))          # 1970-01-01 08:00:00

# format_table：表格渲染
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
]
table = format_table(
    data=data,
    column_names=["模式", "任务数", "耗时(s)"],
)
print(table)
```

## cluster_by_value_sorted 示例

```python
from celestialflow.runtime.util_format import cluster_by_value_sorted

input_dict = {"A": 2, "B": 0, "C": 2, "D": 1}
result = cluster_by_value_sorted(input_dict)
print(result)  # {0: ['B'], 1: ['D'], 2: ['A', 'C']}
```
