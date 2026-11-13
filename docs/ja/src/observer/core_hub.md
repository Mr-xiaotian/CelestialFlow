# src/celestialflow/observer/core_hub.py

> 📅 最終更新日: 2026/11/13

`core_hub.py` は観測者の**ディスパッチセンター** `ObserverHub` を定義します。これ自体も `Observer` であり、受け取った各イベントを登録順に登録済みの観測者へ転送し、型ごとに観測者を検索する `find()` を提供します。ノードと各下流観測者の間のブロードキャストハブです。

## ObserverHub

```python
class ObserverHub(Observer):
    def __init__(self) -> None: ...

    def add_observer(self, observer: Observer) -> None: ...

    def find[O: Observer](self, observer_type: type[O]) -> O | None: ...

    def on_event(self, event: Event) -> None: ...
```

## イベントディスパッチ

`on_event` は現在の観測者スナップショットを走査し、各観測者に対して `observer.on_event(event)` を呼び出します。ある観測者のコールバックが例外を送出した場合、その観測者自身の `handle_exception` に処理を渡します。`handle_exception` 自身がさらに例外を送出した場合、hub 自身の `handle_exception` が最終フォールバックとなります。どちらの場合も他の観測者への配信を中断せず、フレームワークの実行経路へも逃げません。

```python
def on_event(self, event: Event) -> None:
    for observer in self._snapshot():
        try:
            observer.on_event(event)
        except Exception as exception:
            try:
                observer.handle_exception(exception)
            except Exception as fallback:
                self.handle_exception(fallback)
```

> エントリが `on_event` の 1 つだけであるため、新しいイベント型を追加しても hub を変更する必要はありません。すべての観測者がすべてのイベントを受け取り、それぞれ `match` の分岐で処理します。

## 登録とコピーオンライト

観測者リストは **copy-on-write（コピーオンライト）** を採用します：

- 書き込み側は `add_observer()` で `_write_lock` の保護下、新しい不変タプルで `_observers` を丸ごと置き換えます；
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

## 型による観測者の検索

```python
def find[O: Observer](self, observer_type: type[O]) -> O | None:
```

検索ルール：

1. まず**自層**に直接登録された観測者を走査し、最初の `isinstance` 一致者を返します（したがってサブクラスのインスタンスも一致します）；
2. 自層で見つからない場合、登録順にネストされた `ObserverHub` へ再帰的に入って検索します；
3. すべてで見つからない場合は `None` を返します。

したがって**呼び出し側に近い登録ほど優先されます**。

典型的な用途は、ノードが結果を読み取る際にライフサイクル観測者を特定することです：単独実行時は `LifecycleObserver` がノードの hub に直接登録され、グラフスケジューリング時はグラフレベルの hub に存在し、`find` は再帰的に両方をヒットします：

```python
from celestialflow.persist import LifecycleObserver

lifecycle = node.observers.find(LifecycleObserver)
db_path = lifecycle.db_path if lifecycle is not None else None
```

## 使用例

### 登録とブロードキャスト

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

### ネストされた hub と find

```python
from celestialflow.observer import ObserverHub
from celestialflow.persist import LifecycleObserver

graph_hub = ObserverHub()
graph_hub.add_observer(LifecycleObserver())

node_hub = ObserverHub()
node_hub.add_observer(graph_hub)  # ノードはグラフレベルの観測者を共有

found = node_hub.find(LifecycleObserver)
print(found is not None)  # True、find は graph_hub へ再帰的に入る
```

## 組み立てシーン

ノードの観測者 hub は `BaseTaskNode` が保持し、通常はグラフレベルの hub がネストされています。組み立て（`assembly/core_run.py`）フェーズでは：

- `MetricsObserver` が書き込みモデルとして登録されます；
- `LifecycleObserver` / `LogObserver`（`persist` モジュール由来）が登録され、自身が `LifecycleInlet` / `LogInlet` と spout を駆動してディスクへの永続化を完了します；
- 報告を有効にすると `PushSnapshotHandler` / `PushInlet` も登録されます。

これらはすべて `observers.add_observer(...)` で hub に接続されます。ノードは `hub.on_event(...)` にブロードキャストするだけで、具体的な観測者の詳細を認識しません。

## 注意事項

1. **スレッドセーフ**：`add_observer` は実行期に呼び出せます。読み取り側はロックなしでもスナップショットを安全にイテレーションできます。
2. **例外は逃げない**：単一の観測者の例外は hub 内に隔離され、同一バッチの他の観測者を中断せず、ノードの実行経路にも戻りません。
3. **自体も Observer**：`ObserverHub` は `Observer` を継承するため、別の hub に登録できます（それゆえ循環検出が必要です）。
4. **`find` の優先度**：まず自層、次にネスト層；同じ型の複数インスタンスがある場合は最初にヒットしたものだけを返します。
