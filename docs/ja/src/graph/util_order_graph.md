# OrderGraph とグラフアルゴリズムユーティリティ

> 📅 最終更新日: 2026/08/31

`graph/util_order_graph.py` は、最小限のグラフ構造 `OrderGraph` と、それを中心とする一連の基礎的なグラフアルゴリズムを提供します。

このファイルの現在の位置付けは次のとおりです：

- フレームワーク内部に軽量かつ安定した順序を持つグラフ構造を提供します。
- グラフ解析機能の一部を担い、サードパーティのグラフ構造への依存を軽減します。
- `TaskGraph`、ランタイム推定、テストに対して統一されたグラフ解析基盤を提供します。

## 主な能力

### グラフ構造

- `OrderGraph`
  - 最小の順序付き有向グラフ。
  - ノード順序を登録順に安定的に保持します。
  - 出辺と入辺の隣接リストを同時に保持します。

### 基本操作

- `add_node(name)`：ノードを追加します。冪等です。
- `add_edge(u, v)`：有向辺を追加します。端点ノードを自動的に補完し、重複を除去します。
- `nodes`：登録順にすべてのノードを返します。
- `out_edges`：出辺隣接リストの参照ビューを返します（**内部ストレージと共有されるため、呼び出し側は変更しないでください**）。
- `in_edges`：入辺隣接リストの参照ビューを返します（**内部ストレージと共有されるため、呼び出し側は変更しないでください**）。
- `successors(name)`：後続ノードを返します。
- `predecessors(name)`：前駆ノードを返します。
- `has_node(name)`：ノードが存在するかどうかを判定します。
- `from_edges(out_edges, stage_names=None)`：隣接リストから `OrderGraph` を構築します。

### グラフアルゴリズム

- `in_degree(graph)`：各ノードの人次数を計算します。
- `is_dag(graph)`：Kahn アルゴリズムを使用して DAG かどうかを判定します。
- `topo_sort(graph)`：トポロジカル順序を返します。環が存在する場合は `None` を返します。
- `tarjan_scc(graph)`：Tarjan アルゴリズムを使用して強連結成分を計算します。
- `node_to_scc_index(sccs)`：ノードから SCC インデックスへのマッピングを構築します。
- `get_condensation(graph)`：SCC 縮約グラフを構築します。
- `source_sccs(graph)`：縮約グラフで入次数が 0 の強連結成分を返します。
- `source_nodes(graph)`：各ソース SCC から代表ノードを抽出します。
- `compute_node_levels(graph)`：ノード階層を計算します。DAG と環を含むグラフの両方をサポートします。

## 設計上の特徴

### なぜ `list` ではないか

`OrderGraph` の `_nodes` は内部的に `list[str]` ではなく `dict[str, None]` を使用します。その理由は次の 2 つを同時に満たす必要があるためです：

- ノード存在判定が高速であること。
- ノード走査順序が安定していること。

`list` を使用した場合、重複除去と存在チェックはいずれも線形複雑度になります。通常の `set` を使うと存在チェックは高速ですが、順序が安定しません。`dict` はここで「順序付き集合」と等価であり、このシナリオにより適しています。

### なぜ順序を保持するのか

グラフ解析自体は必ずしも固定の走査順序を必要としませんが、フレームワーク内部では安定順序の方が一般的に有利です：

- デバッグ出力を再現しやすくする。
- テスト結果をより安定させる。
- 階層解析とトポロジー結果が構築時の登録順序により近くなる。

## 階層計算の説明

`compute_node_levels(graph)` の処理方針は次のとおりです：

1. まず元のグラフを強連結成分分解します。
2. 各 SCC を縮約グラフのノードに圧縮します。
3. 縮約グラフ（DAG）上でトポロジカル伝播を行います。
4. SCC 階層を元のノードにマッピングします。

したがって：

- DAG の通常のノードは、最長前駆パスによって階層が決められます。
- 環を含むグラフでは、同じ環内のノードは同じ階層を共有します。

この階層アルゴリズムは現在の `TaskGraph` のグラフ解析プロセスに直接使用され、外部のグラフオブジェクトには依存しなくなりました。

## `TaskGraph` との関係

`TaskGraph` は現在 `_build_analysis()` フェーズで `OrderGraph` に基づいて直接以下を完了します：

- ソースノードの識別
- DAG 判定
- ノード階層計算
- ランタイムのグローバル pending 推定に必要なトポロジーと前駆アクセス

## 使用例

### 基本的なグラフ構築

```python
from celestialflow.graph.util_order_graph import OrderGraph, is_dag, topo_sort

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("A", "C")
graph.add_edge("B", "D")
graph.add_edge("C", "D")

print(graph.nodes)  # ('A', 'B', 'C', 'D')
print(graph.successors("A"))  # ('B', 'C')
print(graph.predecessors("D"))  # ('B', 'C')
print(is_dag(graph))  # True
print(topo_sort(graph))  # ['A', 'B', 'C', 'D']
```

### 強連結成分と縮約グラフ

```python
from celestialflow.graph.util_order_graph import (
    OrderGraph,
    get_condensation,
    tarjan_scc,
)

graph = OrderGraph()
graph.add_edge("A", "B")
graph.add_edge("B", "C")
graph.add_edge("C", "A")
graph.add_edge("C", "D")

sccs = tarjan_scc(graph)
cond, _ = get_condensation(graph)

print(sccs)
print(cond.nodes)
print(cond.out_edges)
```

### ノード階層

```python
from celestialflow.graph.util_order_graph import OrderGraph, compute_node_levels

graph = OrderGraph()
graph.add_edge("Input", "Clean")
graph.add_edge("Clean", "Parse")
graph.add_edge("Parse", "Store")

levels = compute_node_levels(graph)
print(levels)
```

## 使用上の推奨事項

- 軽量なグラフ構造と基礎的なグラフアルゴリズムのみが必要な場合は、優先的に `OrderGraph` を使用してください。
- `TaskGraph` の現在の解析ロジックとの一貫性を保つ必要がある場合は、ここにあるアルゴリズム関数を優先して使用してください。
- 印刷可能なグラフ構造テキストをエクスポートする必要がある場合は、`util_render.py` を併用してください。
