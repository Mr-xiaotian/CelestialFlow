# クローンユーティリティテスト (test_clone.py)

> 📅 最終更新日: 2026/06/28

## 役割

`celestialflow.utils.util_clone` の `clone_executor`、`clone_stage`、`clone_graph` の 3 つのクローン関数を検証し、ディープコピー後の新しいオブジェクトが元のオブジェクトと属性が一致し、かつ相互に独立していることを確認します。

## コアテスト対象

- `clone_executor`: `TaskExecutor` をコピーし、`name`、`func`、`execution_mode` を保持。
- `clone_stage`: `TaskStage` をコピーし、`name`、`func`、`execution_mode`、`stage_mode` を保持。
- `clone_graph`: `TaskGraph` をコピーし、完全な DAG 構造（ノード、エッジ、`schedule_mode`）を保持し、ノード間が相互に独立。

## 主要テストシナリオ

### `clone_executor`
- クローン後、`name` / `func` / `execution_mode` が元のオブジェクトと同じであること
- クローンが異なるオブジェクトであること（`is not` チェック）
- クローンの `execution_mode` を変更しても元のオブジェクトに影響しないこと

### `clone_stage`
- クローン後、`name` / `func` / `execution_mode` / `stage_mode` が元のオブジェクトと同じであること
- クローンが異なるオブジェクトであること
- クローンの `execution_mode` を変更しても元の stage に影響しないこと

### `clone_graph`
- 単純 DAG（A→B→C）：クローン後、ソースノード、NetworkX ノード集合、エッジ集合がすべて一致
- `schedule_mode` が正しく保持されること
- クローングラフ内で特定ノードの `execution_mode` を変更しても、元のグラフの対応ノードに影響しないこと
- デフォルトのローカルイベントクライアントはクローン後もインスタンスが独立していること。

## テストカバレッジマトリクス

| テスト関数 | カバレッジ目標 |
|----------|----------|
| `test_clone_executor_same_attributes` | クローン後の主要属性が一致すること |
| `test_clone_executor_different_object` | クローンが新しいオブジェクトを返すこと |
| `test_clone_executor_independent` | クローンの変更が元の実行器に影響しないこと |
| `test_clone_stage_same_attributes` | クローン後の主要属性が一致すること |
| `test_clone_stage_different_object` | クローンが新しいオブジェクトを返すこと |
| `test_clone_stage_independent` | クローンの変更が元の stage に影響しないこと |
| `test_clone_graph_structure` | DAG 構造、ソースノード、エッジ、`schedule_mode` が一致すること |
| `test_clone_graph_independent` | クローングラフのノード変更が元のグラフに影響しないこと |
| `test_clone_graph_creates_independent_local_event_client` | ローカルイベントクライアントのインスタンスが独立していること |

## 実行方法

```bash
# すべて実行
pytest tests/utils/test_clone.py -v

# executor クローンテストのみ実行
pytest tests/utils/test_clone.py -k "executor" -v

# stage クローンテストのみ実行
pytest tests/utils/test_clone.py -k "stage" -v

# graph クローンテストのみ実行
pytest tests/utils/test_clone.py -k "graph" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------|------|
| `TestUtilClone` | ~0.1s |

## 重要な詳細

- グラフクローン時に NetworkX グラフでノードとエッジの一貫性を検証し、ソースノードアクセスが同時に `_build_analysis` をトリガーします。
- `clone_graph` テストは有向非巡回グラフ `A → B → C` を構築し、グラフ構造の完全性を検証します。
- `LocalEventClient` の独立検証により、クローングラフが独立したイベントバスを持ち、ランタイム状態が相互に干渉しないことを確認します。

## 注意事項

- クローンユーティリティは `benchmark_graph` 内部でグラフ構造をコピーし、異なるモード組み合わせの独立実行を実現するために使用されます。
- 関連実装は `src/celestialflow/utils/util_clone.py` にあります。
