# グラフ解析ユーティリティテスト (test_utilgraph.py)

> 📅 最終更新日: 2026/06/22

## 役割
`celestialflow.graph.util_graph` の基礎グラフ解析関数を検証し、`OrderGraph` 構築、階層計算、ソースノード検索ロジックの正確性を確認します。

## コアテスト対象
- `OrderGraph.from_edges`: 隣接リストを `OrderGraph` に変換。
- `compute_node_levels`: グラフ内の各ノードの論理階層を計算。
- `source_nodes`: グラフの入口ノード（ソースノード）を検索。

## 主要テストフロー
1. **グラフ構築テスト**: 線形、循環あり、孤立ノードのシナリオをカバーし、ノード数・エッジ数と方向を検証。
2. **階層計算テスト**:
   - **DAG**: 線形チェーン、ファンアウト構造の階層増加を検証。
   - **循環グラフ**: 強連結成分（SCC）内のノードが同一階層を共有することを検証。
   - **非連結グラフ**: 各連結成分が独立して第0層から計算されることを検証。
3. **ソースノード検索テスト**:
   - **DAG**: 入次数0のノードを検索。
   - **純粋な循環**: SCC全体をソースとみなし、代表点を1つ返す。
   - **ホイールトポロジ**: 中心ノードが唯一のソースとして識別されることを検証。

## テストの重点
- **OrderGraph 構築**: 内部順序グラフ構造と隣接関係が正しいことを確認。
- **階層の一貫性**: 複雑なトポロジ（尾付き循環など）における階層計算の堅牢性。
- **SCC 処理**: 循環参照が無限ループや誤った階層分布を引き起こさないことを確認。

## 実行方法

```bash
# すべて実行
pytest tests/graph/test_utilgraph.py -v

# グラフ構築テストのみ実行
pytest tests/graph/test_utilgraph.py::TestBuildOrderGraph -v

# 階層計算テストのみ実行
pytest tests/graph/test_utilgraph.py -k "levels" -v

# ソースノード検索テストのみ実行
pytest tests/graph/test_utilgraph.py -k "source" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestBuildOrderGraph` | < 0.1s（純粋なメモリ計算） |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## 重要な詳細
- テストケースはすべて純粋なメモリ計算で、実行速度が非常に速い。

## 注意事項
- テストコードは `tests/graph/test_utilgraph.py` にあり、対応する実装は `src/celestialflow/graph/util_graph.py` にあります。
