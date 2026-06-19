# RuntimeEstimators

> 📅 最后更新日期: 2026/06/18

`runtime/util_estimators.py` 提供运行时耗时估算函数。

## 主要函数

- `calc_remaining(processed, pending, elapsed)`：估算节点剩余时间。
- `calc_elapsed(status, last_elapsed, last_pending, interval)`：按状态累计耗时。
- `calc_global_pending(graph, processed_map, pending_map)`：基于 DAG 与观测指标估算全局待处理任务数。

## 使用示例

以下示例展示 `RemainingTimeEstimator` 相关函数的用法。

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

### calc_global_pending：基于 DAG 估算全局待处理任务数

```python
from celestialflow.graph.util_graph import OrderGraph
from celestialflow.runtime.util_estimators import calc_global_pending

# 构建一个简单的 DAG: A -> B -> C
graph = OrderGraph.from_edges({"A": ["B"], "B": ["C"]}, ("A", "B", "C"))

# 输入观测数据
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(graph, processed_map, pending_map)
for node, pending in result.items():
    print(f"节点 {node}: 预计待处理 {pending} 个任务")
```

## 用途

- 驱动监控面板 ETA 展示。
- 辅助识别潜在拥塞节点。
