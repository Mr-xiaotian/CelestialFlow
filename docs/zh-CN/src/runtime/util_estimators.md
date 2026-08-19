# RuntimeEstimators

> 📅 最后更新日期: 2026/08/19

`runtime/util_estimators.py` 提供运行时耗时估算函数。

## 主要函数

- `calc_remaining(processed, pending, elapsed)`：基于均值估算节点剩余时间。
- `calc_elapsed(status, last_elapsed, last_pending, interval)`：按状态累计耗时。
- `format_avg_time(elapsed, processed)`：格式化平均处理速度（秒/任务或任务/秒）。

## 使用示例

以下示例展示 `calc_remaining`、`calc_elapsed`、`format_avg_time` 等估算函数的用法。

### calc_remaining：估算节点剩余时间

```python
from celestialflow.runtime.util_estimators import calc_remaining

# 已处理 80 个，剩余 20 个，已消耗 40 秒
remaining = calc_remaining(
    processed=80,
    pending=20,
    elapsed=40.0,
)
print(f"预计剩余时间: {remaining:.2f} 秒")  # 10.0 秒 (20/80 * 40)

# 无已处理数据时返回 0
remaining_zero = calc_remaining(processed=0, pending=100, elapsed=10.0)
print(f"无历史数据: {remaining_zero} 秒")  # 0
```

### calc_elapsed：按状态累计已耗时间

```python
from celestialflow.runtime.util_types import StageStatus
from celestialflow.runtime.util_estimators import calc_elapsed

# 节点正在运行，上次已耗 30 秒，上次待处理 5 个，采集间隔 2 秒
elapsed = calc_elapsed(
    status=StageStatus.RUNNING,
    last_elapsed=30.0,
    last_pending=5,
    interval=2.0,
)
print(f"更新后已耗时间: {elapsed:.1f} 秒")  # 32.0 (30 + 2)

# 节点已停止，已耗时间不再增加
elapsed_stopped = calc_elapsed(
    status=StageStatus.STOPPED,
    last_elapsed=50.0,
    last_pending=0,
    interval=2.0,
)
print(f"已停止节点: {elapsed_stopped:.1f} 秒")  # 50.0（不再增加）
```

### format_avg_time：格式化平均处理速度

```python
from celestialflow.runtime.util_estimators import format_avg_time

# 每个任务耗时 >= 1s 时显示 s/it
print(format_avg_time(200.0, 100))  # 2.00s/it

# 每个任务耗时 < 1s 时显示 it/s（取倒数）
print(format_avg_time(12.5, 100))  # 8.00it/s

# 无数据
print(format_avg_time(0.0, 0))  # N/A
```

## 用途

- 驱动监控面板 ETA 展示。
