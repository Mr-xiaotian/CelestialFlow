# GraphEstimators

> 📅 最終更新日: 2026/09/16

`graph/util_estimators.py` は、タスクグラフ（DAG）に基づくグローバルな未処理タスク数の推定関数を提供します。

## 主な関数

### calc_global_pending

```python
def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
    downstream_map: dict[str, dict[str, int]],
) -> dict[str, int]: ...
```

タスクグラフ（DAG）に基づいて、各ノードのグローバルな未処理タスク数を見積もります（やや保守的 / 輻輳増幅型）。

#### 基本思想

1. 各ノードの「既知タスク量」を `seen = processed + pending` と定義する
2. 上流・下流の組み合わせごとに独立した増幅係数 `scale[u][w]` を保持する。これは上流 u が下流 w へ送る予測出力量を表す：

   ```
   scale[u][w] = total_u * output_u->w / max(1, proc_u)
   ```

   ここで出力比率 `output_u->w / proc_u` は u 自身の単一スナップショット（`proc_u` と同源で一致）から算出され、ノード間のスナップショット時刻差の影響を回避する。
3. 各ノードの「予測総入力タスク量 `total`」を逐次推定する：

   ```
   total_v = external_v + sum(scale[u][v] for u in preds(v))
   ```

   ここで `external_v = max(0, seen_v - sum(output_u->v))` は外部注入タスク数であり、上流による増幅を受けない。
4. 予測残タスク数は `max(pending_v, total_v - processed_v)` となり、少なくとも現在観測されている `pending` を保持する。

#### アルゴリズム特性

- **下流ごとの独立増幅**：各下流は上流からの実際の出力比率に応じて独立に増幅される。ファンアウト分割やスプリッターの倍率出力も明示的に記録される
- **出力比率の単側化**：出力比率は送信側自身のスナップショットから計算されるため、`proc = 0` のとき係数は自然に 0 となり、病的な増幅は発生しない
- **やや保守的な推定**：上流の積み上がりを下流へ明示的に増幅するため、監視・アラート・ボトルネック識別に適している
- **入力要件**：タスクグラフは有向非巡回グラフ（DAG）でなければならず、そうでない場合は `ValueError` が発生します

#### パラメータ

| パラメータ | 型 | 説明 |
|------|------|------|
| `graph` | `OrderGraph` | タスク依存グラフ。ノードは map のキーと対応している必要があります |
| `processed_map` | `dict[str, int]` | 各ノードで既に完了したタスク数 |
| `pending_map` | `dict[str, int]` | 各ノードの現在の残りタスク数 |
| `downstream_map` | `dict[str, dict[str, int]]` | 各ノードが各下流へ実際に送ったタスク数。形式は `{node: {downstream_name: count}}`。欠落したノードや下流は 0 として扱います |

#### 戻り値

`dict[str, int]` — 各ノードの予測未処理タスク数。

## 使用例

```python
from celestialflow.graph.util_order_graph import OrderGraph
from celestialflow.graph.util_estimators import calc_global_pending

# 単純な DAG を構築: A -> B -> C
graph = OrderGraph()
for u, v in [("A", "B"), ("B", "C")]:
    graph.add_edge(u, v)

# 観測データを入力
processed_map = {"A": 100, "B": 50, "C": 10}
pending_map = {"A": 0, "B": 50, "C": 90}

# 各ノードが各下流へ実際に送ったタスク数
downstream_map = {"A": {"B": 100}, "B": {"C": 50}}

result = calc_global_pending(graph, processed_map, pending_map, downstream_map)
for node, pending in result.items():
    print(f"ノード {node}: 予測未処理 {pending} 件のタスク")
```

## 用途

- `TaskGraph.collect_runtime_snapshot()` から呼び出され、モニタリングパネルに DAG を考慮したグローバルな残タスク推定を提供します
- 潜在的な輻輳ノードの識別に役立ちます