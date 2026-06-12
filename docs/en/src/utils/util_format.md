# UtilsFormat

> 📅 Last Updated: 2026/04/22

`utils/util_format.py` provides general formatting utilities.

## Key Functions

- `format_repr`: Safely truncates object string representations.
- `format_table`: Renders 2D data as a text table.
- `format_duration`: Converts seconds to a readable duration.
- `format_timestamp`: Converts a timestamp to a date-time string.
- `format_avg_time`: Formats average processing speed.

## Usage Examples

### Complete Examples for format_repr / format_table / format_duration / format_timestamp / format_avg_time

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
print("1. format_repr: Safely truncate object strings")
print("=" * 50)

# Short strings are not truncated
print(format_repr("hello world", 50))  # hello world

# Long strings are truncated (first 2/3 + ... + last 1/3)
long_str = "A" * 30 + "B" * 30 + "C" * 30
print(f"Truncated result: {format_repr(long_str, 30)}")

expected = "AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC"
print(f"Actual length: {len(format_repr(long_str, 30))}")  # 30 + 3(...)

# Newlines and backslashes are escaped
print(format_repr("line1\nline2\\back", 50))  # line1\nline2\\back

# ====== 2. format_duration ======
print("\n" + "=" * 50)
print("2. format_duration: Convert seconds to readable duration")
print("=" * 50)

print(f"format_duration(0):       {format_duration(0)}")        # 00:00
print(f"format_duration(59):      {format_duration(59)}")       # 00:59
print(f"format_duration(60):      {format_duration(60)}")       # 01:00
print(f"format_duration(3661):    {format_duration(3661)}")     # 01:01:01
print(f"format_duration(86399):   {format_duration(86399)}")    # 23:59:59

# ====== 3. format_timestamp ======
print("\n" + "=" * 50)
print("3. format_timestamp: Convert timestamp to date string")
print("=" * 50)

now = time.time()
print(f"Current timestamp: {now}")
print(f"Formatted: {format_timestamp(now)}")  # 2026-05-24 14:30:00

# Fixed timestamps
print(f"Epoch start: {format_timestamp(0)}")            # 1970-01-01 08:00:00
print(f"2026 New Year: {format_timestamp(1767225600)}")  # 2026-01-01 08:00:00 (UTC+8)

# ====== 4. format_avg_time ======
print("\n" + "=" * 50)
print("4. format_avg_time: Format average processing speed")
print("=" * 50)

# When avg time per task >= 1s, displays as s/it
print(f"100 tasks in 200s: {format_avg_time(200.0, 100)}")   # 2.00s/it
print(f"1 task in 5s:     {format_avg_time(5.0, 1)}")       # 5.00s/it

# When avg time per task < 1s, displays as it/s (reciprocal)
print(f"100 tasks in 12.5s: {format_avg_time(12.5, 100)}")  # 8.00it/s
print(f"500 tasks in 2s:    {format_avg_time(2.0, 500)}")   # 250.00it/s

# Edge case
print(f"No data: {format_avg_time(0.0, 0)}")                 # N/A

# ====== 5. format_table (comprehensive) ======
print("\n" + "=" * 50)
print("5. format_table: Render text tables")
print("=" * 50)

# Basic table
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
    ["async", 100, 0.45],
]
table = format_table(
    data=data,
    row_names=None,  # use default row numbers
    column_names=["Mode", "Task Count", "Time (s)"],
    align="left",
)
print(table)
# +---+--------+------------+----------+
# | # | Mode   | Task Count | Time (s) |
# +---+--------+------------+----------+
# | 0 | serial | 100        | 2.34     |
# | 1 | thread | 100        | 0.89     |
# | 2 | async  | 100        | 0.45     |
# +---+--------+------------+----------+

# Table with row names
perf_data = [[0.12, 500], [0.08, 800], [0.05, 1200]]
table2 = format_table(
    data=perf_data,
    row_names=["Serial", "Thread", "Async"],
    column_names=["Avg Time (s/it)", "Throughput (it/s)"],
    align="right",
)
print(f"\nRight-aligned table:\n{table2}")
```
