# src/celestialflow/observer/__init__.py

> 📅 最終更新日: 2026/11/13

`observer` モジュールは CelestialFlow の**可観測性モジュール**であり、観測者プロトコル、統一イベント型、イベントディスパッチセンター、および内蔵の指標・進捗出力観測者を担当します。

## エクスポートシンボル

モジュールレベルの `__all__` は以下の通り完全にエクスポートします：

```python
__all__ = [
    "Event",
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
]
```

エクスポートシンボルは次の表で分類できます：

| エクスポートシンボル | ソースモジュール | 説明 |
|---------|---------|------|
| `Event` | `core_event` | すべての観測イベントの基底クラス。型識別のみを担い、状態を持ちません |
| `Observer` | `core_observer` | 観測者基底クラス。統一された `on_event(event)` と `handle_exception(exception)` のみを宣言 |
| `ObserverHub` | `core_hub` | 観測者ディスパッチセンター。それ自体も `Observer` であり、登録順にイベントを転送し、`find()` を提供 |
| `MetricsObserver` | `core_metrics` | グラフレベル指標観測者（書き込みモデル + 読み取り専用ビュー）。イベントに基づいてノードカウントと状態を維持 |
| `PrintObserver` | `core_print` | `print` ベースのコンソール観測者。ローカルデバッグやサンプルデモに便利 |
| `NodeStartEvent` / `NodeEndEvent` | `core_event` | ノード起動 / 終了イベント |
| `TaskInputEvent` / `TaskSuccessEvent` / `TaskFailEvent` / `TaskSkipEvent` / `TaskRetryEvent` | `core_event` | タスク入力 / 成功 / 失敗 / スキップ / リトライイベント |
| `TerminationInputEvent` / `TerminationMergeEvent` | `core_event` | 終了シグナル入力 / マージイベント |
| `GraphStartEvent` / `GraphEndEvent` | `core_event` | タスクグラフ起動 / 終了イベント |

## ファイル説明

1. **core_observer.py**（`Observer`）
   - **役割**: 実行器ライフサイクル観測者の基底クラス。`on_event` と `handle_exception` のみを宣言。
   - **特徴**: すべてのイベントは単一のエントリから入り、サブクラスは `match` で型ごとにディスパッチします。基底クラスは `ABC` ではありません。

2. **core_event.py**（`Event` + 11 個のイベント `dataclass`）
   - **役割**: 統一イベント基底クラスと、タスク / ノード / タスクグラフのライフサイクルにあるすべてのイベント型を定義。
   - **特徴**: 具体的なイベントはいずれも `frozen=True, slots=True` の読み取り専用データクラス；`Event` は `__slots__ = ()` を使用し状態を持ちません。

3. **core_hub.py**（`ObserverHub`）
   - **役割**: 観測者ディスパッチセンター。受け取った各イベントを登録順に登録済み観測者へ転送；`find()` は型ごとに観測者を再帰的に検索。
   - **特徴**: それ自体も `Observer`；観測者リストは copy-on-write（書き込み時コピー）。

4. **core_metrics.py**（`MetricsObserver`）
   - **役割**: グラフレベル指標観測者。イベントに基づいて各ノードのカウント、状態、実行開始時間を維持。
   - **特徴**: 観測者として書き込みを行うと同時に、`MetricsView` プロトコルを通じて読み取り専用の `NodeMetrics` スナップショットを公開。

5. **core_print.py**（`PrintObserver`）
   - **役割**: すぐに使えるコンソール観測者。
   - **特徴**: スレッドセーフな `ValueWrapper` で `total` / `succeeded` / `failed` / `skipped` を集計し、`[name] ...` プレフィックスで出力。

## モジュール連携

### 内部連携
- `Observer` は観測者パターンの基底クラス；`ObserverHub` と `MetricsObserver`、`PrintObserver` はいずれも `Observer` のサブクラス。
- `core_event.py` で定義されたイベント型は `core_observer` / `core_hub` / `core_metrics` / `core_print` が共通で参照。

### 外部連携
- **Node モジュールとの連携**: `BaseTaskNode` は `ObserverHub observers` を保持し、イベント発生時にイベントを構築して `hub.on_event(...)` を呼び出してブロードキャスト；結果を読み取る際は `observers.find(LifecycleObserver)` でライフサイクル観測者を特定し `db_path` を取得します。
- **Persist モジュールとの連携**: `LifecycleObserver` / `LogObserver` は `Observer` のサブクラスであり、`run_node_resources` / `run_graph_resources` が hub に登録し、イベントを消費してディスクへ永続化します。
- **Assembly モジュールとの連携**: `assembly/core_run.py` が `ObserverHub` を組み立て、`MetricsObserver`、`LifecycleObserver`、`LogObserver` などを登録。

## アーキテクチャ特性

### イベント駆動とディスパッチ
- **単一エントリ**: すべての観測者は `on_event(event)` のみを実装し、イベントオブジェクトは `core_event.py` で定義された読み取り専用 `dataclass` で、豊富なフィールドを持ちます。
- **明示的なライフサイクルタイムスタンプ**: ノード / タスクグラフの開始・終了時刻はイベントフィールド（`start_time` / `end_time`）が持ち、観測者が自ら `time.time()` でサンプリングする必要はありません。
- **マルチキャスト配信**: `ObserverHub` は一度に登録済みの全観測者へ同一イベントをブロードキャスト。
- **例外分離**: 単一の観測者コールバックが送出した例外は hub が捕捉し、その観測者自身の `handle_exception` に委譲します。**他の観測者への配信は中断されず**、フレームワークの実行パスにも逃げません。

## 使用例

```python
from celestialflow.observer import (
    Event,
    MetricsObserver,
    Observer,
    ObserverHub,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_event(self, event: Event) -> None:
        match event:
            case TaskSuccessEvent():
                print(f"{event.node} 成功: {event.result_repr}")
            case _:
                pass


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

登録済みの観測者を検索：

```python
from celestialflow.observer import ObserverHub, PrintObserver

hub = ObserverHub()
hub.add_observer(PrintObserver("StageA"))

printer = hub.find(PrintObserver)
print(printer.name if printer is not None else None)  # StageA
```

## 注意事項

1. **インポートパス**: 上記のシンボルは `celestialflow.observer` からインポートしてください。旧版の `celestialflow.observability` ではありません。
2. **指標と進捗を分離**: 構造化されたノード指標が必要な場合は `MetricsObserver` を、コンソールの進捗出力だけでよい場合は `PrintObserver` を使用します。
3. **観測者は `on_event` のみを実装**: 旧版の `on_node_start` / `on_task_success` などの個別コールバックはすべて削除されました。
