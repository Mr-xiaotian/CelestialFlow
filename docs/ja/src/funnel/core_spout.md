# BaseSpout

> 📅 最終更新日: 2026/05/15

`BaseSpout` はすべての Spout クラスの基底クラスで、バックグラウンドスレッドでキューを監視しレコードを処理する共通機能を提供します。

## 初期化

```python
class BaseSpout:
    def __init__(self):
        self.queue = Queue()  # キュー
        self._thread: Thread | None = None
```

## コアメソッド

### start

バックグラウンド監視スレッドを開始します。

```python
def start(self):
    """バックグラウンド監視スレッドを開始する。"""
```

フロー：
1. `_before_start()` フックを呼び出す
2. デーモンスレッドを作成・開始し、`_spout()` メソッドを実行する

### stop

監視スレッドを停止し、リソースをクリーンアップします。

```python
def stop(self):
    """監視スレッドを停止し、リソースをクリーンアップする。"""
```

フロー：
1. `TERMINATION_SIGNAL` をキューに送信する
2. スレッドの終了を待機（`join`）し、`_thread` を `None` に設定する
3. `_after_stop()` フックを呼び出す

### get_queue

```python
def get_queue(self) -> Queue:
    """Inlet 側で使用するキューオブジェクトを返す。"""
```

## オーバーライド可能なメソッド

```python
def _before_start(self):
    """開始前の初期化処理。"""

def _handle_record(self, record):
    """単一レコードを処理する（サブクラスで必ずオーバーライド）。"""
    raise NotImplementedError

def _after_stop(self):
    """停止後のクリーンアップ処理。"""
```

## 内部実装

```python
def _spout(self):
    """監視ループ。バックグラウンドスレッドで実行される。"""
    while True:
        try:
            record = self.queue.get(timeout=0.5)
            if isinstance(record, TerminationSignal):
                break
            self._handle_record(record)
        except Empty:
            continue
        except Exception:
            continue
```

## 注意事項

1. **スレッドセーフ**: `queue.Queue` を使用してスレッド間通信の安全性を確保
2. **デーモンスレッド**: 監視スレッドはデーモンスレッドとして設定され、メインプロセス終了時に自動的に終了
3. **グレースフルな停止**: `TerminationSignal` を送信してスレッドに停止を通知
4. **キューのクリーンアップ**: 停止時にキュー内の残りのレコードはクリーンアップされない
