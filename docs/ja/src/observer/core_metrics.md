# src/celestialflow/observer/core_metrics.py

> 📅 最終更新日: 2026/10/09

`core_metrics.py` は**グラフレベル指標観測者** `MetricsObserver` を定義します。これは「書き込みモデル」と「読み取り専用ビュー」の 2 つの役割を同時に担います：観測者としてイベントから各ノードのカウント、状態、実行開始時間を書き込み、読み取り専用ビューを通じて不変の `NodeMetrics` スナップショットを公開します。

## MetricsObserver

```python
class MetricsObserver(Observer):
    def __init__(self) -> None: ...

    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    def on_task_input(self, event: TaskInputEvent) -> None: ...
    def on_task_success(self, event: TaskSuccessEvent) -> None: ...
    def on_task_fail(self, event: TaskFailEvent) -> None: ...
    def on_task_skip(self, event: TaskSkipEvent) -> None: ...

    def get_node_metrics(self, node: str) -> NodeMetrics | None: ...
    def get_graph_metrics(self) -> dict[str, NodeMetrics]: ...
```

単一インスタンスは 1 つの実行スコープにサービスします：タスクグラフ全体、または単独実行の単一ノード。

## イベント書き込みロジック

MetricsObserver は以下のイベントのみに関心を持って指標を維持します：

| イベント | 書き込み動作 |
|------|---------|
| `on_node_start` | そのノードの状態を `RUNNING` に設定し、ウォールクロックの開始時間を記録 |
| `on_node_end` | そのノードの状態を `STOPPED` に設定 |
| `on_task_input` | 発生源を区別：`from_node is None` の場合は外部注入カウントを加算；それ以外は受信側の上流カウントと発信元側の下流カウントの両方を加算 |
| `on_task_success` | そのノードの成功カウントを加算 |
| `on_task_fail` | そのノードの失敗カウントを加算 |
| `on_task_skip` | そのノードのスキップカウントを加算 |

ストレージセルは最初のイベントで**オンデマンドに確立**され（`_ensure`、冪等）、辺カウントも実際のタスクフローによってインクリメンタルに書き込まれるため、グラフ構築期の構造イベントには依存しません。上流の配信は受信側の上流カウントと発信元側の下流カウントの両方に書き込むため、ノード間でカウンタオブジェクトを共有する必要も、ノードタイプごとに統計ロジックを特化する必要もありません。

## 読み取り専用ビュー

読み取りは `runtime.util_types.MetricsView` プロトコルを通じて公開され、不変の `NodeMetrics` スナップショットを返します：

- `get_node_metrics(node)`：単一ノードの指標スナップショットを取得；ノードが未登録の場合は `None` を返します。
- `get_graph_metrics()`：全グラフの全ノードの指標スナップショット（`{node: NodeMetrics}`）を返します。

`NodeMetrics` は読み取り専用 DTO（`runtime.util_types`）で、フィールドは次のとおりです：

| フィールド | 説明 |
|------|------|
| `node` | ノード名 |
| `status` | ノードのライフサイクル状態（`NodeStatus`） |
| `start_time` | ノードが実行状態に入ったウォールクロック時間（秒）。未起動は `0.0` |
| `external_input` | 外部注入タスク数 |
| `upstream_input` | 上流提供タスク数 |
| `input_total` | 入力総数（外部注入 + 上流提供） |
| `succeeded` / `failed` / `skipped` | 成功 / 失敗 / スキップタスク数 |
| `processed` | 処理済み数（成功 + 失敗 + スキップ） |
| `pending` | 待機数（`max(0, input_total - processed)`） |
| `upstream_counts` / `downstream_counts` | 各上流 / 下流ノードのタスク数量マッピング |

## 使用例

```python
from celestialflow.observer import ObserverHub, MetricsObserver


metrics = MetricsObserver()
hub = ObserverHub()
hub.add_observer(metrics)

# ... タスクグラフの実行後 ...

for node_name, nm in metrics.get_graph_metrics().items():
    print(node_name, nm.succeeded, nm.failed, nm.skipped, nm.pending)
```

## ノード / 組み立てとの関係

- `BaseTaskNode` はカウントと `TaskMetrics` を**自力では保持しません**。ノードカウントは `MetricsObserver` がイベントに基づいて一元的に維持します。
- 組み立てフェーズ（`assembly/core_run.py`）で `MetricsObserver` を作成してノードの `ObserverHub` に登録し、その読み取り専用ビューを `LogInlet` とスナップショットハンドラに横断的に提供します。

## 注意事項

1. **単一スコープのインスタンス**：1 つの `MetricsObserver` は 1 つの実行スコープにサービスします。異なるグラフ / ノード間での再利用を避けてカウントの串刺しを防止します。
2. **スレッドセーフ**：内部のすべてのストレージアクセスは `_lock` の保護下で行われます。
3. **構造はイベント駆動**：グラフ構築期の構造イベントには依存せず、タスクイベントが発生したノードに即座にストレージセルを確立できます。