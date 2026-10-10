# src/celestialflow/observer/__init__.py

> 📅 最終更新日: 2026/10/09

`observer` モジュールは CelestialFlow の**可観測性モジュール**であり、観測者プロトコル、タスク / ノード / タスクグラフのイベント型、イベントディスパッチセンター、および内蔵の指標・進捗出力観測者を担当します。

## エクスポートシンボル

モジュールレベルの `__all__` は以下を完全にエクスポートします：

```python
__all__ = [
    "GraphEndEvent",
    "GraphStartEvent",
    "MetricsObserver",
    "NodeEndEvent",
    "NodeStartEvent",
    "Observer",
    "ObserverHub",
    "PrintObserver",
    "TaskFailEvent",
    "TaskInputEvent",
    "TaskRetryEvent",
    "TaskSkipEvent",
    "TaskSuccessEvent",
    "TerminationInputEvent",
    "TerminationMergeEvent",
    "WorkerCrashEvent",
]
```

エクスポートシンボルは次の表で分類できます：

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `Observer` | `core_observer` | 観測者基底クラス。タスク / ノード / グラフの全ライフサイクルコールバックインターフェースを宣言。全コールバックはデフォルトで空実装 |
| `ObserverHub` | `core_hub` | 観測者ディスパッチセンター。それ自体も `Observer` であり、登録順にイベントを転送 |
| `MetricsObserver` | `core_metrics` | グラフレベル指標観測者（書き込みモデル + 読み取り専用ビュー）。イベントに基づいてノードカウントと状態を維持 |
| `PrintObserver` | `core_observer_print` | `print` ベースのコンソール観測者。ローカルデバッグやサンプルデモに便利 |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | ノード起動 / 終了イベント |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | タスク入力 / 成功 / 失敗 / スキップ / リトライイベント |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | 終了シグナル入力 / マージイベント |
| `WorkerCrashEvent` | `core_event` | ワーカークラッシュイベント |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | タスクグラフ起動 / 終了イベント |

## ファイル説明

1. **core_observer.py**（`Observer`）
   - **役割**: 実行器ライフサイクル観測者の基底クラス。12 個のイベントコールバックと `handle_exception` を宣言。
   - **特徴**: すべてのコールバックはデフォルトの空実装を提供。ABC ではなく、サブクラスが必要に応じてオーバーライド。

2. **core_event.py**（12 個のイベント `dataclass`）
   - **役割**: タスク / ノード / タスクグラフのライフサイクルにあるすべてのイベント型を定義。
   - **特徴**: いずれも `frozen=True, slots=True` の読み取り専用データクラスであり、観測者コールバックの引数として使用。

3. **core_hub.py**（`ObserverHub`）
   - **役割**: 観測者ディスパッチセンター。受け取った各イベントを登録順に登録済み観測者へ転送。
   - **特徴**: それ自体も `Observer`；観測者リストは copy-on-write（書き込み時コピー）。

4. **core_metrics.py**（`MetricsObserver`）
   - **役割**: グラフレベル指標観測者。イベントに基づいて各ノードのカウント、状態、実行開始時間を維持。
   - **特徴**: 観測者として書き込みを行うと同時に、`MetricsView` プロトコルを通じて読み取り専用の `NodeMetrics` スナップショットを公開。

5. **core_observer_print.py**（`PrintObserver`）
   - **役割**: すぐに使えるコンソール観測者。
   - **特徴**: スレッドセーフな `ValueWrapper` で `total` / `succeeded` / `failed` / `skipped` を集計し、`[name] ...` プレフィックスで出力。

## モジュール連携

### 内部連携
- `Observer` は観測者パターンの基底クラス；`ObserverHub` と `MetricsObserver`、`PrintObserver` はすべて `Observer` のサブクラス。
- `core_event.py` で定義されたイベント型は `core_observer` / `core_hub` / `core_metrics` / `core_observer_print` が共通で参照。

### 外部連携
- **Node モジュールとの連携**: `BaseTaskNode` は `ObserverHub observers` を保持し、イベント発生時に `hub.on_*()` を呼び出してブロードキャスト。
- **Persist モジュールとの連携**: `run_node_resources` / `run_graph_resources` が `LifecycleInlet` / `LogInlet` を観測者として hub に登録し、イベントを消費してディスクに永続化。
- **Assembly モジュールとの連携**: `assembly/core_run.py` が `ObserverHub` を組み立て、`MetricsObserver`、`LifecycleInlet`、`LogInlet` などを登録。

## アーキテクチャ特性

### イベント駆動とディスパッチ
- **イベントオブジェクトがコールバック引数**: すべてのコールバックは `core_event.py` で定義された読み取り専用 `dataclass` を受け取り、豊富なフィールドを持ちます。
- **マルチキャスト配信**: `ObserverHub` は一度に登録済みの全観測者へ同一イベントをブロードキャスト。
- **例外分離**: 単一の観測者コールバックが送出した例外は hub が捕捉し、その観測者自身の `handle_exception` に委譲します。**他の観測者への配信は中断されず**、フレームワークの実行パスにも逃げません。

## 使用例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    TaskSuccessEvent,
    MetricsObserver,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## 注意事項

1. **インポートパス**: 上記のシンボルは `celestialflow.observer` からインポートしてください。旧版の `celestialflow.observability` ではありません。
2. **指標と進捗を分離**: 構造化されたノード指標が必要な場合は `MetricsObserver` を、コンソールの進捗出力だけでよい場合は `PrintObserver` を使用します。