# グラフ解析ユーティリティテスト (test_order_graph.py)

> 📅 最終更新日: 2026/08/31

## 役割
`celestialflow.graph.util_order_graph` の基礎グラフ解析能力を検証します。`OrderGraph` 構築、階層計算（`compute_node_levels`）、ソースノード検索（`source_nodes`）、SCC 分割（`tarjan_scc`）、および深さが Python のデフォルト再帰上限（約 1000）を超える場合の反復アルゴリズムのリグレッションを含みます。

## コアテスト対象
- `OrderGraph.from_edges` / `add_node` / `add_edge` / `successors`: 順序付きグラフ構造の構築とクエリ。
- `compute_node_levels`: グラフ内の各ノードの論理階層を計算（SCC 内で階層を共有）。
- `source_nodes`: グラフの入口ノード（ソースノード）を検索。SCC は代表点1つのみを返す。
- `tarjan_scc`: 強連結成分分割（反復実装）。
- `DEEP = 5000`: Python のデフォルト再帰上限を超える深鎖/深環規模。反復版 `tarjan_scc` のリグレッション用。

## テストカバレッジマトリックス

| テストクラス | ケース数 | カバレッジ対象 | 主なアサーション |
|------------|---------|------------|----------------|
| `TestBuildOrderGraph` | 3 | 線形鎖 / 循環あり / 孤立ノードのグラフ構築 | ノード数、エッジ総数、`successors` 隣接方向が正しい |
| `TestComputeNodeLevels` | 5 | 線形 DAG、ファンアウト DAG、単純循環、尾付き循環、非連結グラフ | 階層が単調増加、B/C 同層、循環内で階層共有、尾は循環より1層高い、各連結成分が独立に0から開始 |
| `TestFindSourceNodes` | 4 | 線形 DAG、複数ソース、純粋な循環、ホイール型トポロジ | 入次数0のソースノード、純粋な循環 SCC は代表点1つを返す、Center は唯一の source |
| `TestDeepGraphRegression` | 3 | 5000 ノードの深鎖 / 深環 / TaskGraph 経由のフルチェーン構築 | 深鎖の SCC は全て単点、RecursionError なし、深環は単一 SCC に収束、`get_stages_summary` / `get_source_names` / `get_graph_analysis` が正常動作 |
| **合計** | **15** | | |

## 主要テストフロー

1. **グラフ構築** (`TestBuildOrderGraph`): 線形（A→B→C）、循環（C→A で閉じる）、孤立ノードをカバーし、ノード数・エッジ数と隣接方向を検証。
2. **階層計算** (`TestComputeNodeLevels`):
   - **DAG**: 線形鎖の階層が単調増加。ファンアウト構造で B、C が同層。
   - **循環グラフ**: SCC 内ノードが同一階層を共有。尾付き循環では、尾ノードが循環より1層高い。
   - **非連結グラフ**: 各部分が独立に第0層から計算される。
3. **ソースノード検索** (`TestFindSourceNodes`):
   - **DAG**: 入次数が0のノードを返す（順序非依存の `set` アサーション可能）。
   - **純粋な循環**: SCC 全体をソースとみなし、代表点を1つ返す。
   - **ホイール型トポロジ**: Center が Ring 状の環を指し、Center が唯一の source。
4. **深グラフリグレッション** (`TestDeepGraphRegression`):
   - 深鎖（5000 ノード）：`tarjan_scc` は全て単点 SCC、ソースノードは `n0`、階層は 0 から 4999 へ線形に増加。
   - 深環（5000 ノード）：全ノードが単一 SCC に収束。
   - 深鎖を `TaskGraph`（`graph_mode="thread"`）経由でフルチェーン構築・解析してもクラッシュせず、`layersDict[4999] == ["n4999"]`、`get_stages_summary()` は 5000 ステージを返し、`get_source_names() == ["n0"]`。

## テストヘルパー関数
- `_make_graph(edges)`: エッジ定義（暗黙に出現する下流ノードを含む）からテストグラフを構築。
- `_make_chain(depth)`: `depth` ノードの線形鎖を構築。
- `_make_ring(size)`: `size` ノードの閉ループを構築。

## テストの重点
- **OrderGraph 構築**: 内部の順序付きグラフ構造と隣接関係が正しいことを確認。
- **階層の一貫性**: 複雑なトポロジ（尾付き循環など）における階層計算の堅牢性。
- **SCC 処理**: 循環参照が無限ループや誤った階層/ソースノード分布を引き起こさないことを確認。
- **再帰安全性**: `tarjan_scc` はかつて再帰実装であり、深鎖/深環で `RecursionError` をトリガーしていました。反復実装への移行後、超深グラフでも解析が正常に完了するはず。

## 実行方法

```bash
# 全部実行
pytest tests/graph/test_order_graph.py -v

# グラフ構築テストのみ
pytest tests/graph/test_order_graph.py::TestBuildOrderGraph -v

# 階層計算テストのみ
pytest tests/graph/test_order_graph.py::TestComputeNodeLevels -v

# ソースノード検索テストのみ
pytest tests/graph/test_order_graph.py::TestFindSourceNodes -v

# 深グラフリグレッションテストのみ
pytest tests/graph/test_order_graph.py::TestDeepGraphRegression -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestBuildOrderGraph` | < 0.1s（純粋なメモリ計算） |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |
| `TestDeepGraphRegression` | ~1s（5000 ノード規模、純粋なメモリ計算） |

## 重要な詳細
- `TestDeepGraphRegression.test_deep_chain_through_taskgraph` を除き、すべて純粋なメモリ計算であり、実行速度は非常に高速です。
- 深グラフのケースでは `DEEP` を 5000 に保っており、リグレッションカバーとテスト所要時間のバランスを取っています。

## 注意事項
- テストコードは `tests/graph/test_order_graph.py` にあり、対応する実装は `src/celestialflow/graph/util_order_graph.py` にあります。
