# BaseInlet

> 📅 最終更新日: 2026/04/22

`BaseInlet` はすべての Inlet クラスの基底クラスで、レコードをキューに書き込む共通機能を提供します。

## 初期化

```python
class BaseInlet:
    def __init__(self, queue):
        self.queue = queue  # 対応する Spout の get_queue() から取得
```

## コアメソッド

### _funnel

```python
def _funnel(self, record):
    """レコードをキューに入れ、対応する Spout に消費させる。"""
    self.queue.put(record)
```

## 使用例

```python
from celestialflow.funnel import BaseSpout, BaseInlet

class MySpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

class MyInlet(BaseInlet):
    def send(self, data):
        self._funnel(data)

# 使用方法
spout = MySpout()
spout.start()
inlet = MyInlet(spout.get_queue())
inlet.send("hello")
spout.stop()
```
