# グラフ解析ツールテスト (test_analysis.py)

> 📅 最終更新日: 2026/05/23

## 役割
`celestialflow.graph.util_analysis` モジュールのグラフ解析ツール関数を検証し、グラフ構築、階層計算、ソースノード検索ロジックの正確性を確認します。

## コアテスト対象
- `build_networkx_graph`: 隣接リストを NetworkX 有向グラフに変換。
- `compute_node_levels`: グラフ内の各ノードの論理階層を計算。
- `find_source_nodes`: グラフの入口ノード（ソースノード）を検索。

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
- **NetworkX 統合**: 内部データ構造の変換が正しいことを確認。
- **階層の一貫性**: 複雑なトポロジ（尾付き循環など）における階層計算の堅牢性。
- **SCC 処理**: 循環参照が無限ループや誤った階層分布を引き起こさないことを確認。

## 実行方法

```bash
# 全テスト実行
pytest tests/graph/test_analysis.py -v

# グラフ構築テストのみ
pytest tests/graph/test_analysis.py::TestBuildNetworkxGraph -v

# 階層計算テストのみ
pytest tests/graph/test_analysis.py -k "levels" -v

# ソースノード検索テストのみ
pytest tests/graph/test_analysis.py -k "source" -v
```

## パフォーマンス参考

| テスト | 所要時間 |
|--------|---------|
| `TestBuildNetworkxGraph` | < 0.1s（純粋なメモリ計算） |
| `TestComputeNodeLevels` | < 0.1s |
| `TestFindSourceNodes` | < 0.1s |

## 重要な詳細
- 軽量な Mock オブジェクトを使用して `Stage` および `Runtime` 環境をシミュレート。
- テストケースはすべて純粋なメモリ計算で、実行速度が非常に速い。

## 注意事項
- テストコードは `tests/graph/test_analysis.py` にあり、対応する実装は `src/celestialflow/graph/util_analysis.py` にあります。
