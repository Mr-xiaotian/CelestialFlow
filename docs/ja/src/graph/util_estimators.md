# GraphEstimators

> 📅 最終更新日: 2026/08/31

`graph/util_estimators.py` は、タスクグラフ（DAG）に基づくグローバルな未処理タスク数の推定関数を提供します。

## 主な関数

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
) -> dict[str, int]: ...
```

タスクグラフ（DAG）に基づいて、各ノードのグローバルな未処理タスク数を見積もります（やや保守的 / 輻輳増幅型）。

#### 基本思想

1. 各ノードの「既知タスク量」を `seen = processed + pending` と定義する
2. 下流ノードの現在の既知タスクは、すべての上流ノードから均等に由来すると仮定する（複数上流の等寄与仮定）
3. トポロジカル順に従って DAG 上で各ノードの「予測総入力タスク量 `total`」を逐次推定し、それに基づき増幅係数 `scale` を計算する
4. 予測残タスク数は少なくとも現在観測されている `pending` を保持する

#### アルゴリズム特性

- **複数上流の等寄与仮定**：異なる上流の実際の出力比率を区別しない
- **やや保守的な推定**：増幅基準として `processed` を使用するため、システムの初期段階や深刻な積み上がり時には大きな推定値が生成される
- **入力要件**：タスクグラフは有向非巡回グラフ（DAG）でなければならず、そうでない場合は `ValueError` が発生します

#### パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `graph` | `OrderGraph` | タスク依存グラフ。ノードは map のキーと対応している必要があります |
| `processed_map` | `dict[str, int]` | 各ノードで既に完了したタスク数 |
| `pending_map` | `dict[str, int]` | 各ノードの現在の残りタスク数 |

#### 戻り値

`dict[str, int]` — 各ノードの予測未処理タスク数。

## 使用例

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# 単純な DAG を構築: A -> B -> C
graph = OrderGraph.from_edges({"A": ["B"], "B": ["C"]}, ("A", "B", "C"))

# 観測データを入力
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

result = calc_global_pending(graph, processed_map, pending_map)
for node, pending in result.items():
    print(f"ノード {node}: 予測未処理 {pending} 件のタスク")
```

## 用途

- `TaskGraph.collect_runtime_snapshot()` から呼び出され、モニタリングパネルに DAG を考慮したグローバルな残タスク推定を提供します
- 潜在的な輻輳ノードの識別に役立ちます
