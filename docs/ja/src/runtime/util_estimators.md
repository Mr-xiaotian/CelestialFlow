# RuntimeEstimators

> 📅 最終更新日: 2026/07/16

`runtime/util_estimators.py` は実行時経過時間推定関数を提供します。

## 主要関数

- `calc_remaining(processed, pending, elapsed)`: ノードの残り時間を推定します。
- `calc_elapsed(status, last_elapsed, last_pending, interval)`: 状態別に経過時間を累計します。
- `calc_global_pending(graph, processed_map, pending_map)`: DAG と観測メトリクスに基づいてグローバル保留タスク数を推定します。

## 使用例

以下の例は `calc_remaining`、`calc_elapsed`、`calc_global_pending` などの推定関数の使用方法を示します。

### calc_remaining：ノード残り時間の推定

```python
from celestialflow.runtime.util_estimators import calc_remaining

# 処理済み 80、残り 20、経過 40 秒
remaining = calc_remaining(
    processed=80,
    pending=20,
    elapsed=40.0,
)
print(f"推定残り時間: {remaining:.2f} 秒")  # 10.0 秒 (20/80 * 40)

# 処理済みデータがない場合は 0 を返す
remaining_zero = calc_remaining(processed=0, pending=100, elapsed=10.0)
print(f"履歴データなし: {remaining_zero} 秒")  # 0
```

### calc_elapsed：状態別経過時間の累計

```python
from celestialflow.runtime.util_types import StageStatus
from celestialflow.runtime.util_estimators import calc_elapsed

# ノードが実行中、前回経過 30 秒、前回保留 5、収集間隔 2 秒
elapsed = calc_elapsed(
    status=StageStatus.RUNNING,
    last_elapsed=30.0,
    last_pending=5,
    interval=2.0,
)
print(f"更新後経過時間: {elapsed:.1f} 秒")  # 32.0 (30 + 2)

# ノードが停止済み、経過時間は増加しない
elapsed_stopped = calc_elapsed(
    status=StageStatus.STOPPED,
    last_elapsed=50.0,
    last_pending=0,
    interval=2.0,
)
print(f"停止済みノード: {elapsed_stopped:.1f} 秒")  # 50.0（増加しない）
```

### calc_global_pending：DAG に基づくグローバル保留タスク数の推定

```python
from celestialflow.graph.util_graph import OrderGraph
from celestialflow.runtime.util_estimators import calc_global_pending

# 単純な DAG を構築: A -> B -> C
graph = OrderGraph.from_edges({"A": ["B"], "B": ["C"]}, ("A", "B", "C"))

# 観測データを入力
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(graph, processed_map, pending_map)
for node, pending in result.items():
    print(f"ノード {node}: 推定保留 {pending} タスク")
```

## 用途

- 監視パネルの ETA 表示の駆動。
- 潜在的な輻輳ノードの識別補助。
