# test_structure.py テスト説明

> 📅 最終更新日: 2026/05/15

## テスト目的

`TaskLoop` と `TaskWheel` の2つの循環グラフ構造のグラフ分析能力を検証します。以下を含みます：
- DAG 検出（循環グラフは `isDAG=False` を返すべき）
- レベル計算（サイクル内ノードは同レベル、center ノードは別レベル）
- ソースノード推論（`get_source_stages`）

## テスト範囲

| テストクラス | ケース数 | カバレッジ |
|-------------|---------|-----------|
| `TestTaskLoop` | 2 | ループ構造分析、ループ構造 source 推論 |
| `TestTaskWheel` | 2 | ホイール構造分析（center + ring レベル）、ホイール構造 source 推論 |

### 主要テストケースの詳細

#### `test_loop_analysis`
- **目的**: `TaskLoop`（s1 → s2 → s3 → s1）のグラフ分析結果を検証。
- **アサーション**: `isDAG` が `False`；すべてのノードが同レベル。

#### `test_loop_source_stages`
- **目的**: ループ構造の `get_source_stages()` がループ内の代表ノードを返すことを検証。
- **アサーション**: 1つの source を返し、tag がループ内ノードに属する。

#### `test_wheel_analysis`
- **目的**: `TaskWheel`（center → {r1, r2, r3}、r1 → r2 → r3 → r1）のレベル構造を検証。
- **アサーション**: `isDAG` が `False`；center がレベル0、ring ノードがレベル1。

#### `test_wheel_source_stages`
- **目的**: ホイール構造の `get_source_stages()` が center ノードのみを返すことを検証。
- **アサーション**: 1つの source を返し、tag が center の tag と等しい。

## 依存関係

| 依存 | 説明 |
|------|------|
| `celestialflow` | `TaskLoop`、`TaskWheel`、`TaskStage` |

## 実行方法

```bash
pytest tests/test_structure.py -v
```

## パフォーマンス参考

| テスト | 所要時間（Windows / i5） |
|--------|------------------------|
| `TestTaskLoop` | ~2s |
| `TestTaskWheel` | ~2s |

## 関連ファイル

- `src/celestialflow/graph/core_structure.py`: `TaskLoop`、`TaskWheel` 実装
- `src/celestialflow/graph/util_analysis.py`: グラフ分析ユーティリティ関数
- `tests/test_graph.py`: `TaskGraph` およびその他の構造サブクラステスト
