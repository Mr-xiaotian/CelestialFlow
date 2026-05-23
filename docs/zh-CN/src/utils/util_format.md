# UtilsFormat

> 📅 最后更新日期: 2026/04/22

`utils/util_format.py` 提供通用格式化工具。

## 主要函数

- `format_repr`：安全截断对象字符串。
- `format_table`：将二维数据渲染为文本表格。
- `format_duration`：秒数转可读时长。
- `format_timestamp`：时间戳转日期时间字符串。
- `format_avg_time`：格式化平均处理速度。

## 使用示例

### format_repr / format_table / format_duration / format_timestamp / format_avg_time 完整示例

```python
import time
from celestialflow.utils.util_format import (
    format_repr,
    format_table,
    format_duration,
    format_timestamp,
    format_avg_time,
)

# ====== 1. format_repr ======
print("=" * 50)
print("1. format_repr: 安全截断对象字符串")
print("=" * 50)

# 短字符串不会被截断
print(format_repr("hello world", 50))  # hello world

# 长字符串被截断（前 2/3 + ... + 后 1/3）
long_str = "A" * 30 + "B" * 30 + "C" * 30
print(f"截断结果: {format_repr(long_str, 30)}")

expected = "AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC"
print(f"实际长度: {len(format_repr(long_str, 30))}")  # 30 + 3(...)

# 换行和反斜杠被转义
print(format_repr("line1\nline2\\back", 50))  # line1\nline2\\back

# ====== 2. format_duration ======
print("\n" + "=" * 50)
print("2. format_duration: 秒数转可读时长")
print("=" * 50)

print(f"format_duration(0):       {format_duration(0)}")        # 00:00
print(f"format_duration(59):      {format_duration(59)}")       # 00:59
print(f"format_duration(60):      {format_duration(60)}")       # 01:00
print(f"format_duration(3661):    {format_duration(3661)}")     # 01:01:01
print(f"format_duration(86399):   {format_duration(86399)}")    # 23:59:59

# ====== 3. format_timestamp ======
print("\n" + "=" * 50)
print("3. format_timestamp: 时间戳转日期字符串")
print("=" * 50)

now = time.time()
print(f"当前时间戳: {now}")
print(f"格式化后: {format_timestamp(now)}")  # 2026-05-24 14:30:00

# 固定时间戳
print(f"纪元开始: {format_timestamp(0)}")            # 1970-01-01 08:00:00
print(f"2026年元旦: {format_timestamp(1767225600)}")  # 2026-01-01 08:00:00 (UTC+8)

# ====== 4. format_avg_time ======
print("\n" + "=" * 50)
print("4. format_avg_time: 格式化平均处理速度")
print("=" * 50)

# 每个任务耗时 >= 1s 时显示 s/it
print(f"100个任务耗时200s: {format_avg_time(200.0, 100)}")   # 2.00s/it
print(f"1个任务耗时5s:    {format_avg_time(5.0, 1)}")       # 5.00s/it

# 每个任务耗时 < 1s 时显示 it/s（取倒数）
print(f"100个任务耗时12.5s: {format_avg_time(12.5, 100)}")  # 8.00it/s
print(f"500个任务耗时2s:    {format_avg_time(2.0, 500)}")   # 250.00it/s

# 边界情况
print(f"无数据: {format_avg_time(0.0, 0)}")                 # N/A

# ====== 5. format_table (综合应用) ======
print("\n" + "=" * 50)
print("5. format_table: 渲染文本表格")
print("=" * 50)

# 基础表格
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
    ["async", 100, 0.45],
]
table = format_table(
    data=data,
    row_names=None,  # 使用默认行号
    column_names=["模式", "任务数", "耗时(s)"],
    align="left",
)
print(table)
# +---+--------+---------+----------+
# | # | 模式   | 任务数  | 耗时(s)  |
# +---+--------+---------+----------+
# | 0 | serial | 100     | 2.34     |
# | 1 | thread | 100     | 0.89     |
# | 2 | async  | 100     | 0.45     |
# +---+--------+---------+----------+

# 带行名的表格
perf_data = [[0.12, 500], [0.08, 800], [0.05, 1200]]
table2 = format_table(
    data=perf_data,
    row_names=["串行", "线程", "异步"],
    column_names=["平均耗时(s/it)", "吞吐量(it/s)"],
    align="right",
)
print(f"\n右对齐表格:\n{table2}")
```
