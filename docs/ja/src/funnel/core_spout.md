# BaseSpout

> 📅 最終更新日: 2026/04/22

`BaseSpout` はすべての出口クラスの基底クラスで、バックグラウンドスレッドでキューをリスニングしレコードを処理する汎用機能を提供します。

## 初期化

```python
class BaseSpout:
    def __init__(self):
        self.queue = MPQueue()  # マルチプロセス安全なキュー
        self._thread: Thread | None = None
```

## コアメソッド

### start

バックグラウンドリスニングスレッドを起動します。

```python
def start(self):
    """バックグラウンドリスニングスレッドを起動します。"""
```

フロー：
1. `_before_start()` フックを呼び出します
2. `_spout()` メソッドを実行するデーモンスレッドを作成して起動します

### stop

リスニングスレッドを停止し、リソースをクリーンアップします。

```python
def stop(self):
    """リスニングスレッドを停止し、リソースをクリーンアップします。"""
```

フロー：
1. キューに `TERMINATION_SIGNAL` を送信します
2. スレッドの終了を待機します
3. キューリソースをクリーンアップします（`cleanup_mpqueue`）
4. `_after_stop()` フックを呼び出します

### get_queue

```python
def get_queue(self) -> MPQueue:
    """Inlet 側で使用するためのキューオブジェクトを返します。"""
```

## オーバーライド可能なメソッド

```python
def _before_start(self):
    """起動前の初期化操作です。"""

def _handle_record(self, record):
    """単一のレコードを処理します（サブクラスでオーバーライドが必要です）。"""
    raise NotImplementedError

def _after_stop(self):
    """停止後のクリーンアップ操作です。"""
```

## 内部実装

```python
def _spout(self):
    """リスニングループです。バックグラウンドスレッドで実行されます。"""
    while True:
        try:
            record = self.queue.get(timeout=0.5)
            if isinstance(record, TerminationSignal):
                break
            self._handle_record(record)
        except Empty:
            continue
```

## 注意事項

1. **マルチプロセス安全性**: `multiprocessing.Queue` を使用してクロスプロセス通信の安全性を確保します
2. **デーモンスレッド**: リスニングスレッドはデーモンスレッドとして設定され、メインプロセスの終了時に自動的に終了します
3. **グレースフルシャットダウン**: `TerminationSignal` を送信してスレッドに停止を通知します
4. **キューのクリーンアップ**: 停止時にキュー内の残りのレコードがクリーンアップされます
