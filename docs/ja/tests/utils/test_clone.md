# クローンユーティリティテスト (test_clone.py)

> 📅 最終更新日: 2026/05/28

## 目的

`celestialflow.utils.util_clone` 内の `clone_executor`、`clone_stage`、`clone_graph` の 3 つのクローン関数を検証し、ディープコピー後の新しいオブジェクトが元のオブジェクトと属性が同一であり、かつ相互に独立していることを確認します。

## コアテスト対象

- `clone_executor`: `TaskExecutor` をコピーし、`name`、`func`、`execution_mode` を保持します。
- `clone_stage`: `TaskStage` をコピーし、`name`、`func`、`execution_mode`、`stage_mode` を保持します。
- `clone_graph`: `TaskGraph` をコピーし、完全な DAG 構造（ノード、エッジ、`schedule_mode`）を保持し、ノード間が相互に独立しています。

## 主要テストシナリオ

### `clone_executor`
- クローン後の `name` / `func` / `execution_mode` が元のオブジェクトと同じ
- クローンは異なるオブジェクトを返す（`is not` チェック）
- クローンの `execution_mode` を変更しても元のオブジェクトに影響しない

### `clone_stage`
- クローン後の `name` / `func` / `execution_mode` / `stage_mode` が元のオブジェクトと同じ
- クローンは異なるオブジェクトを返す
- クローンの `execution_mode` を変更しても元の stage に影響しない

### `clone_graph`
- 単純 DAG（A→B→C）：クローン後のソースノード、NetworkX ノード集合、エッジ集合がすべて一致
- `schedule_mode` が正しく保持される
- クローングラフでノードの `execution_mode` を変更しても、元のグラフの対応ノードに影響しない

## 実行方法

```bash
# 全実行
pytest tests/utils/test_clone.py -v

# executor クローンテストのみ
pytest tests/utils/test_clone.py -k "executor" -v

# stage クローンテストのみ
pytest tests/utils/test_clone.py -k "stage" -v

# graph クローンテストのみ
pytest tests/utils/test_clone.py -k "graph" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------------|----------|
| `TestUtilClone` | ~0.1s |

## 重要な詳細

- グラフクローン時には NetworkX グラフを介してノードとエッジの一貫性を検証し、ソースノードへのアクセスは同時に `_build_analysis` をトリガーします。
- `clone_graph` テストは有向非巡回グラフ `A → B → C` を構築し、グラフ構造の完全性を検証します。

## 注意事項

- クローンユーティリティは `benchmark_graph` 内部で異なるモード組み合わせの独立実行のためにグラフ構造を複製するのに使用されます。
- 関連実装は `src/celestialflow/utils/util_clone.py` にあります。
