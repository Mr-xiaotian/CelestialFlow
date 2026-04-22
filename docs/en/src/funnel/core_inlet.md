# BaseInlet

`BaseInlet` is the base class for all inlet classes, providing common functionality for writing records to a queue.

## Initialization

```python
class BaseInlet:
    def __init__(self, queue):
        self.queue = queue  # Obtained from the corresponding Spout's get_queue()
```

## Core Methods

### _funnel

```python
def _funnel(self, record):
    """Put a record into the queue for consumption by the corresponding Spout."""
    self.queue.put(record)
```

## Usage Example

```python
from celestialflow.funnel import BaseSpout, BaseInlet

class MySpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

class MyInlet(BaseInlet):
    def send(self, data):
        self._funnel(data)

# Usage
spout = MySpout()
spout.start()
inlet = MyInlet(spout.get_queue())
inlet.send("hello")
spout.stop()
```
