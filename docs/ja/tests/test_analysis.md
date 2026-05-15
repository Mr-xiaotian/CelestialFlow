# test_analysis.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

`celestialflow.graph.util_analysis` モジュールのグラフ分析ユーティリティ関数を検証します。以下を含みます：
- NetworkX 有向グラフの構築（`build_networkx_graph`）
- ノードレベル計算（`compute_node_levels`）、DAG および循環グラフを含む
- ソースノード探索（`find_source_nodes`）、純粋サイクルおよびホイールトポロジーを含む

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestBuildNetworkxGraph` | 3 | 線形グラフ、循環グラフ、孤立ノード |
| `TestComputeNodeLevels` | 5 | 線形 DAG、ファンアウト DAG、単一サイクル、サイクル+テール、切断グラフ |
| `TestFindSourceNodes` | 4 | 線形 DAG、複数ソース、純粋サイクル、ホイールトポロジー |

### 主要テストケースの詳細

#### `test_linear`
- **目的**: A → B → C 線形グラフのノード数、エッジ数、後継関係を検証。
- **アサーション**: 3ノード、2エッジ、A の後継は B。

#### `test_cycle`
- **目的**: 循環グラフ（A → B → C → A）の正しい構築を検証。
- **アサーション**: 3ノード、3エッジ、C の後継に A を含む。

#### `test_isolated_node`
- **目的**: エッジのない孤立ノードグラフを検証。
- **アサーション**: 2ノード、0エッジ。

#### `test_fan_out_dag`
- **目的**: A → {B, C} → D ファンアウト DAG のレベル計算。
- **アサーション**: A はレベル0、B と C はレベル1、D はレベル2。

#### `test_single_cycle`
- **目的**: 純粋サイクル（A → B → C → A）ではすべてのノードが同じ SCC に属し、レベルを共有。
- **アサーション**: A、B、C のレベルが同一。

#### `test_cycle_with_tail`
- **目的**: サイクル（A → B → C → A）にテール（A → D）を加え、D はサイクルより1レベル高い。
- **アサーション**: サイクル内ノードは同レベル、D はサイクルレベル + 1。

#### `test_disconnected`
- **目的**: 2つの独立チェーン（A → B、X → Y）がそれぞれレベル0から開始。

#### `test_pure_cycle`（FindSourceNodes）
- **目的**: 純粋サイクルには `in_degree=0` のノードがないが、SCC 全体が1つの source として返される。
- **アサーション**: 1つの source を返し、サイクル内ノードに属する。

#### `test_wheel_topology`
- **目的**: ホイールトポロジー（Center → {R1, R2, R3}、R1 → R2 → R3 → R1）、Center が唯一の source。

## 依存関係

| 依存 | 説明 |
|------|------|
| `pytest` | テストフレームワーク |
| `networkx` | グラフデータ構造 |
| `celestialflow.graph.util_analysis` | `build_networkx_graph`、`compute_node_levels`、`find_source_nodes` |

## 実行方法

```bash
pytest tests/test_analysis.py -v
```

すべてのテストケースは純粋なインメモリグラフ計算であり、実行時間は `< 100ms` です。

## 関連ファイル

- `src/celestialflow/graph/util_analysis.py`: テスト対象の実装
- `tests/test_graph.py`: `TaskGraph` 統合シナリオで分析関数を間接的に使用
