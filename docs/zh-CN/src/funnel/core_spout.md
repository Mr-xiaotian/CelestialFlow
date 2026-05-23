# BaseSpout

> 📅 最后更新日期: 2026/05/15

`BaseSpout` 是所有出口类的基类，提供后台线程监听队列并处理记录的通用功能。

## 初始化

```python
class BaseSpout:
    def __init__(self):
        self.queue = Queue()  # 队列
        self._thread: Thread | None = None
```

## 核心方法

### start

启动后台监听线程。

```python
def start(self):
    """启动后台监听线程。"""
```

流程：
1. 调用 `_before_start()` 钩子
2. 创建并启动守护线程，执行 `_spout()` 方法

### stop

停止监听线程并清理资源。

```python
def stop(self):
    """停止监听线程并清理资源。"""
```

流程：
1. 发送 `TERMINATION_SIGNAL` 到队列
2. 等待线程结束（`join`），并将 `_thread` 置为 `None`
3. 调用 `_after_stop()` 钩子

### get_queue

```python
def get_queue(self) -> Queue:
    """返回队列对象，供 Inlet 端使用。"""
```

## 可重写方法

```python
def _before_start(self):
    """启动前的初始化操作。"""

def _handle_record(self, record):
    """处理单条记录（子类必须重写）。"""
    raise NotImplementedError

def _after_stop(self):
    """停止后的清理操作。"""
```

## 内部实现

```python
def _spout(self):
    """监听循环，在后台线程中运行。"""
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

## 使用示例

以下示例展示如何创建 `BaseSpout` 的自定义子类，包括启动、处理和停止的全流程。

### 基本子类实现

```python
from queue import Queue
from celestialflow.funnel import BaseSpout

# 自定义 Spout：将字符串记录写入列表
class CollectSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.collected: list[str] = []

    def _handle_record(self, record):
        """处理单条记录，子类必须重写此方法"""
        self.collected.append(str(record))

# 使用
spout = CollectSpout()
spout.start()

# 通过队列发送记录
q = spout.get_queue()
q.put("task_1")
q.put("task_2")
q.put("task_3")

# 停止
spout.stop()
print(f"收集了 {len(spout.collected)} 条记录")
```

### 带生命周期钩子的子类

```python
from queue import Queue
from celestialflow.funnel import BaseSpout

class FileWriterSpout(BaseSpout):
    def __init__(self, filepath: str):
        super().__init__()
        self.filepath = filepath
        self.fh = None

    def _before_start(self):
        """启动前打开文件"""
        self.fh = open(self.filepath, "w", encoding="utf-8")
        print(f"文件已打开: {self.filepath}")

    def _handle_record(self, record):
        """写入文件"""
        line = f"{record}\n"
        self.fh.write(line)

    def _after_stop(self):
        """停止后关闭文件"""
        if self.fh:
            self.fh.close()
            print(f"文件已关闭: {self.filepath}")

# 使用
import tempfile
import os

# 写入临时文件
spout = FileWriterSpout("/tmp/test_spout.log")
spout.start()

spout.get_queue().put("record_alpha")
spout.get_queue().put("record_beta")

spout.stop()

# 验证文件内容
if os.path.exists("/tmp/test_spout.log"):
    with open("/tmp/test_spout.log") as f:
        print(f.read())
    os.remove("/tmp/test_spout.log")
```

### 计数 Spout

```python
from queue import Queue
from celestialflow.funnel import BaseSpout

class CounterSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.count = 0

    def _handle_record(self, record):
        self.count += 1

spout = CounterSpout()
spout.start()

for i in range(100):
    spout.get_queue().put(i)

spout.stop()
print(f"处理了 {spout.count} 条记录")  # 100
```

## 注意事项

1. **线程安全**: 使用 `queue.Queue` 确保线程间通信安全
2. **守护线程**: 监听线程设置为守护线程，主进程退出时自动结束
3. **优雅停止**: 通过发送 `TerminationSignal` 通知线程停止
4. **队列清理**: 停止时不会清理队列中的剩余记录
