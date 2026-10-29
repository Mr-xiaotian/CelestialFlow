# src/celestialflow/runtime/util_format.py

> 📅 最后更新日期: 2026/10/30

`runtime/util_format.py` 提供通用格式化工具函数，包括字符串截断、表格渲染和按值聚类等。

## 主要函数

| 函数 | 说明 |
|------|------|
| `format_repr(obj, max_length)` | 安全截断对象字符串，自动转义换行和反斜杠 |
| `format_table(data, ...)` | 将二维数据渲染为文本表格，支持 `left` / `right` / `center` 对齐 |
| `cluster_by_value_sorted(input_dict)` | 按值聚类，按 value 升序排序 |

## format_repr

```python
def format_repr(obj: Any, max_length: int) -> str: ...
```

将对象格式化为字符串，自动转义换行符和反斜杠，超长时按 `前 2/3 + ... + 后 1/3` 截断：

- 先做 `str(obj)`，再把反斜杠加倍（`\` → `\\`）、把换行符替换为两个字符 `\` + `n`
- `max_length <= 0` 或长度未超限时原样返回（不截断）
- 截断时 `segment_len = max(1, max_length // 3)`，取前 `2 * segment_len` 个字符 + `...` + 末尾 `segment_len` 个字符

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

- `data` 为空时返回字符串 `"表格数据为空！"`
- `column_names` 缺省或数量不足时，按 Excel 风格自动补名；`row_names` 缺省时用 `0..n-1` 作为行号
- 行列长度不一致时用 `fill_value` 填充
- `align` 支持 `"left"` / `"right"` / `"center"`，未知取值回退为左对齐

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
)

# format_repr：安全截断
print(format_repr("hello world", 50))  # hello world
print(format_repr("A" * 100, 30))  # AAAAAAAAAAAAAAAAAAAA...AAAAAAAAAA（20 + 3 + 10）
print(format_repr("a\nb", 50))  # a\nb（换行被转义为字面量 \n）
print(format_repr("A" * 100, 0))  # 不截断，返回完整 100 个 A

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
