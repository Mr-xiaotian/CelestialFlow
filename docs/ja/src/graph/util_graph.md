# OrderGraph とグラフアルゴリズム補助

> 📅 最終更新日: 2026/06/18

`graph/util_graph.py` は最小グラフ構造 `OrderGraph` と、CelestialFlow 内部で使用される基礎グラフアルゴリズム群を提供します。

## 主な機能

- `OrderGraph`
  - 最小順序付き有向グラフ
  - 安定したノード反復順序
  - 出辺と入辺の両方を保持
- `in_degree(graph)`
  - 各ノードの入次数を計算
- `is_dag(graph)`
  - Kahn アルゴリズムで DAG かどうかを判定
- `topo_sort(graph)`
  - DAG の場合にトポロジカル順序を返す
- `tarjan_scc(graph)`
  - Tarjan アルゴリズムで強連結成分を計算
- `get_condensation(graph)`
  - SCC 凝縮グラフを構築
- `source_nodes(graph)`
  - 各 source SCC から代表ノードを 1 つ返す
- `compute_node_levels(graph)`
  - DAG と循環グラフの両方に対応したノード階層を計算

## 設計メモ

- `_nodes` は `list[str]` ではなく `dict[str, None]` を使います。これにより、安定した挿入順序と高速な存在確認を両立できます。
- 実装は意図的に軽量で、純粋なインメモリ構造です。
- 同じグラフ構造が `TaskGraph` の解析と実行時 pending 推定で再利用されます。

## `TaskGraph` との関係

`TaskGraph` は現在 `_build_analysis()` 内で `OrderGraph` を直接使い、以下を行います。

- ソースノード検出
- DAG 判定
- ノード階層計算

また、実行時推定器も DAG 前提の pending 伝播に `OrderGraph` を使用します。

## 使用例

```python
from celestialflow.graph.util_graph import OrderGraph, compute_node_levels, source_nodes

graph = OrderGraph.from_edges(
    {"A": ["B", "C"], "B": ["D"], "C": ["D"]},
    ("A", "B", "C", "D"),
)

print(graph.nodes)
print(source_nodes(graph))
print(compute_node_levels(graph))
```
