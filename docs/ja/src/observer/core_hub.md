# src/celestialflow/observer/core_hub.py

> 📅 最終更新日: 2026/10/09

`core_hub.py` は観測者の**配信センター** `ObserverHub` を定義します。これ自体も `Observer` であり、受け取った各イベントを登録順に登録済みの観測者へ転送します。ノードと各下流観測者の間のブロードキャストハブです。

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    # Observer から継承した 12 のイベントコールバック + handle_exception
    def on_node_start(self, event: NodeStartEvent) -> None: ...
    def on_node_end(self, event: NodeEndEvent) -> None: ...
    # ... 各イベントを順にすべての観測者へ転送 ...
    def on_graph_start(self, event: GraphStartEvent) -> None: ...
    def on_graph_end(self, event: GraphEndEvent) -> None: ...
```

各イベントコールバック（`on_*`）の転送セマンティクスは共通です：現在の観測者スナップショットを走査し、各観測者に対して対応するコールバックを呼び出します。ある観測者のコールバックが例外を送出した場合、その観測者自身の `handle_exception` に処理を渡します。`handle_exception` 自身がさらに例外を送出した場合、hub 自身の `handle_exception` が最終フォールバックとなります。どちらの場合も他の観測者への配信を中断せず、フレームワークの実行経路へも逃げません。

## 登録とコピーオンライト

観測者リストは **copy-on-write（コピーオンライト）** を採用します：

- 書き込み側は `add_observer()` で `_write_lock` の保護下の下、新しい不変タプルで `_observers` を丸ごと置き換えます；
- 読み取り経路 `_snapshot()` は現在の参照を直接返し、ロックもコピーもしません；
- タプルが不変であり、かつ CPython の属性読み取りと置き換えが tear しないため、読み取るのは常に何らかの完全なバージョンのスナップショットであり、イテレーション中に並行変更を心配する必要はありません。

```python
def add_observer(self, observer: Observer) -> None:
    self._reject_cycle(observer)
    with self._write_lock:
        self._observers = (*self._observers, observer)
```

### 循環参照の拒否

`add_observer` は先に `_reject_cycle` を呼び出し、hub の循環参照を形成する登録を拒否します（配信時の無限再帰を防ぐため）：

- `observer is self` の場合、`ConfigurationError` を送出します；
- `observer` が `ObserverHub` の場合、その観測者ツリーに沿って DFS で（直接的・間接的に）現在の hub をすでに保持しているか検査し、保持していれば `ConfigurationError` を送出します。

## 使用例

```python
from celestialflow.observer import (
    Observer,
    ObserverHub,
    MetricsObserver,
    TaskSuccessEvent,
)


class MyObserver(Observer):
    def on_task_success(self, event: TaskSuccessEvent) -> None:
        print(f"{event.node} 成功: {event.result_repr}")


hub = ObserverHub()
hub.add_observer(MyObserver())
hub.add_observer(MetricsObserver())
```

## 組み立てシーン

ノードの観測者 hub は `BaseTaskNode` が保持します。組み立て（`assembly/core_run.py`）フェーズでは：

- `MetricsObserver` が書き込みモデルとして登録されます；
- `LifecycleInlet` / `LogInlet`（`persist` モジュール由来）が登録され、イベントを消費してディスクへ書き込みます；
- 報告を有効にすると `PushSnapshotHandler` / `PushInlet` も登録されます。

これらはすべて `observers.add_observer(...)` で同じ hub に接続されます。ノードは `hub.on_*()` にブロードキャストするだけで、具体的な観測者の詳細を認識しません。

## 注意事項

1. **スレッドセーフ**：`add_observer` は実行期に呼び出せます。読み取り側はロックなしでもスナップショットを安全にイテレーションできます。
2. **例外は逃げない**：単一の観測者の例外は hub 内に隔離され、同一バッチの他の観測者を中断せず、ノードの実行経路にも戻りません。
3. **自体も Observer**：`ObserverHub` は `Observer` を継承するため、別の hub に登録できます（それゆえ循環検出が必要です）。