# クローンユーティリティテスト (test_clone.py)

> 📅 最終更新日: 2026/08/26

## 役割

`celestialflow.benchmark.util_clone` の `clone_executor`、`clone_stage`、`clone_graph` の 3 つのクローン関数を検証し、ディープコピー後の新しいオブジェクトが元のオブジェクトと属性が一致し、かつ相互に独立していることを確認します。

## コアテスト対象

- `clone_executor`: `TaskExecutor` をコピーし、`name`、`func`、`execution_mode` を保持。
- `clone_stage`: `TaskStage` をコピーし、`name`、`func`、`execution_mode` などの初期化パラメータを保持。
- `clone_graph`: `TaskGraph` をコピーし、完全な DAG 構造（ノード、エッジ）と `graph_mode` を保持し、ノード間が相互に独立。

## 主要テストシナリオ

### `clone_executor`
- クローン後、`name` / `func` / `execution_mode` が元のオブジェクトと同じであること
- クローンが異なるオブジェクトであること（`is not` チェック）
- クローンの `execution_mode` を変更しても元のオブジェクトに影響しないこと

### `clone_stage`
- クローン後、`name` / `func` / `execution_mode` が元のオブジェクトと同じであること
- クローンが異なるオブジェクトであること
- クローンの `execution_mode` を変更しても元の stage に影響しないこと

### `clone_graph`
- 単純 DAG（A→B→C）：クローン後、ソースノード、`OrderGraph` ノード集合、出边隣接リストがすべて一致
- クローングラフ内で特定ノードの `execution_mode` を変更しても、元のグラフの対応ノードに影響しないこと
- デフォルトのローカルイベントクライアントはクローン後もインスタンスが独立していること
- `TaskReporter` 付きのグラフはクローン後に新しい reporter インスタンスにバインドされること（`cloned.reporter.task_graph is cloned`）

## テストカバレッジマトリクス

| テスト関数 | カバレッジ目標 |
|----------|--------------|
| `test_clone_executor_same_attributes` | クローン後の主要属性が一致すること |
| `test_clone_executor_different_object` | クローンが新しいオブジェクトを返すこと |
| `test_clone_executor_independent` | クローンの変更が元の実行器に影響しないこと |
| `test_clone_stage_same_attributes` | クローン後の主要属性が一致すること |
| `test_clone_stage_different_object` | クローンが新しいオブジェクトを返すこと |
| `test_clone_stage_independent` | クローンの変更が元の stage に影響しないこと |
| `test_clone_graph_structure` | DAG 構造、ソースノード、`OrderGraph` ノードとエッジが一致すること |
| `test_clone_graph_independent` | クローングラフのノード変更が元のグラフに影響しないこと |
| `test_clone_graph_creates_independent_local_event_client` | ローカルイベントクライアントのインスタンスが独立していること |
| `test_clone_graph_rebinds_task_reporter_to_cloned_graph` | `TaskReporter` 付きのグラフがクローン後に新しい reporter インスタンスにバインドされること |

## 実行方法

```bash
# すべて実行
pytest tests/benchmark/test_clone.py -v

# executor クローンテストのみ実行
pytest tests/benchmark/test_clone.py -k "executor" -v

# stage クローンテストのみ実行
pytest tests/benchmark/test_clone.py -k "stage" -v

# graph クローンテストのみ実行
pytest tests/benchmark/test_clone.py -k "graph" -v
```

## パフォーマンス参考

| テストクラス | 所要時間 |
|--------|------|
| `TestUtilClone` | ~0.1s |

## 重要な詳細

- グラフクローン後、`get_order_graph()` が返す `OrderGraph` でノード集合と出边隣接リストの一致を検証します。`get_source_names()` へのアクセスは同時にクローングラフの `_build_analysis` をトリガーします。
- `clone_graph` テストは有向非巡回グラフ `A → B → C` を構築し、グラフ構造の完全性を検証します。
- `LocalEventClient` の独立検証により、クローングラフが独立したイベントバスを持ち、ランタイム状態が相互に干渉しないことを確認します。
- `TaskReporter` 付きのグラフはクローン後に新しい reporter インスタンスにバインドされ、`cloned.reporter.task_graph` はクローングラフを指します。

## 注意事項

- クローンユーティリティは `benchmark_graph` 内部でグラフ構造をコピーし、異なるモード組み合わせの独立実行を実現するために使用されます。
- 関連実装は `src/celestialflow/benchmark/util_clone.py` にあります。
