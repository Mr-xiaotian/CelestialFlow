# UtilsFormat

> 📅 最終更新日: 2026/07/16

`utils/util_format.py` は汎用フォーマットツールを提供します。

## 主要関数

- `format_repr`: オブジェクト文字列を安全に切り詰め。
- `format_table`: 二次元データをテキストテーブルにレンダリング。`left` / `right` / `center` の 3 種類の配置に対応。
- `format_duration`: 秒数を可読な時間形式に変換。
- `format_timestamp`: タイムスタンプを日時文字列に変換。
- `format_avg_time`: 平均処理速度をフォーマット。

## 使用例

### format_repr / format_table / format_duration / format_timestamp / format_avg_time の完全な例

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
print("1. format_repr: オブジェクト文字列の安全な切り詰め")
print("=" * 50)

# 短い文字列は切り詰められない
print(format_repr("hello world", 50))  # hello world

# 長い文字列は切り詰められる（前半 2/3 + ... + 後半 1/3）
long_str = "A" * 30 + "B" * 30 + "C" * 30
print(f"切り詰め結果: {format_repr(long_str, 30)}")

expected = "AAAAAAAAAAAAAAAAAAAA...CCCCCCCCCC"
print(f"実際の長さ: {len(format_repr(long_str, 30))}")  # 30 + 3(...)

# 改行とバックスラッシュはエスケープされる
print(format_repr("line1\nline2\\back", 50))  # line1\nline2\\back

# ====== 2. format_duration ======
print("\n" + "=" * 50)
print("2. format_duration: 秒数を可読な時間形式に変換")
print("=" * 50)

print(f"format_duration(0):       {format_duration(0)}")        # 00:00
print(f"format_duration(59):      {format_duration(59)}")       # 00:59
print(f"format_duration(60):      {format_duration(60)}")       # 01:00
print(f"format_duration(3661):    {format_duration(3661)}")     # 01:01:01
print(f"format_duration(86399):   {format_duration(86399)}")    # 23:59:59

# ====== 3. format_timestamp ======
print("\n" + "=" * 50)
print("3. format_timestamp: タイムスタンプを日付文字列に変換")
print("=" * 50)

now = time.time()
print(f"現在のタイムスタンプ: {now}")
print(f"フォーマット後: {format_timestamp(now)}")  # 2026-05-24 14:30:00

# 固定タイムスタンプ
print(f"エポック開始: {format_timestamp(0)}")            # 1970-01-01 08:00:00
print(f"2026年元旦: {format_timestamp(1767225600)}")  # 2026-01-01 08:00:00 (UTC+8)

# ====== 4. format_avg_time ======
print("\n" + "=" * 50)
print("4. format_avg_time: 平均処理速度のフォーマット")
print("=" * 50)

# タスクあたりの時間 >= 1s の場合、s/it を表示
print(f"100タスク 200s: {format_avg_time(200.0, 100)}")   # 2.00s/it
print(f"1タスク 5s:    {format_avg_time(5.0, 1)}")       # 5.00s/it

# タスクあたりの時間 < 1s の場合、it/s を表示（逆数を取る）
print(f"100タスク 12.5s: {format_avg_time(12.5, 100)}")  # 8.00it/s
print(f"500タスク 2s:    {format_avg_time(2.0, 500)}")   # 250.00it/s

# 境界ケース
print(f"データなし: {format_avg_time(0.0, 0)}")                 # N/A

# ====== 5. format_table（総合応用）======
print("\n" + "=" * 50)
print("5. format_table: テキストテーブルのレンダリング")
print("=" * 50)

# 基本テーブル
data = [
    ["serial", 100, 2.34],
    ["thread", 100, 0.89],
    ["async", 100, 0.45],
]
table = format_table(
    data=data,
    row_names=None,  # デフォルトの行番号を使用
    column_names=["モード", "タスク数", "時間(s)"],
    align="left",
)
print(table)
# +---+--------+---------+----------+
# | # | モード | タスク数 | 時間(s)  |
# +---+--------+---------+----------+
# | 0 | serial | 100     | 2.34     |
# | 1 | thread | 100     | 0.89     |
# | 2 | async  | 100     | 0.45     |
# +---+--------+---------+----------+

# 行名付きテーブル
perf_data = [[0.12, 500], [0.08, 800], [0.05, 1200]]
table2 = format_table(
    data=perf_data,
    row_names=["直列", "スレッド", "非同期"],
    column_names=["平均時間(s/it)", "スループット(it/s)"],
    align="right",
)
print(f"\n右寄せテーブル:\n{table2}")
```
