# BaseInlet

`BaseInlet` 是所有入口类的基类，提供将记录写入队列的通用功能。

## 初始化

```python
class BaseInlet:
    def __init__(self, queue):
        self.queue = queue  # 由对应 Spout 的 get_queue() 获取
```

## 核心方法

### _funnel

```python
def _funnel(self, record):
    """将记录放入队列，供对应的 Spout 消费。"""
    self.queue.put(record)
```

## 使用示例

```python
from celestialflow.funnel import BaseSpout, BaseInlet

class MySpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

class MyInlet(BaseInlet):
    def send(self, data):
        self._funnel(data)

# 使用
spout = MySpout()
spout.start()
inlet = MyInlet(spout.get_queue())
inlet.send("hello")
spout.stop()
```
