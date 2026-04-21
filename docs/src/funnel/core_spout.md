# BaseSpout

`BaseSpout` 是所有出口类的基类，提供后台线程监听队列并处理记录的通用功能。

## 初始化

```python
class BaseSpout:
    def __init__(self):
        self.queue = MPQueue()  # 多进程安全队列
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
2. 等待线程结束
3. 清理队列资源（`cleanup_mpqueue`）
4. 调用 `_after_stop()` 钩子

### get_queue

```python
def get_queue(self) -> MPQueue:
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
```

## 注意事项

1. **多进程安全**: 使用 `multiprocessing.Queue` 确保跨进程通信安全
2. **守护线程**: 监听线程设置为守护线程，主进程退出时自动结束
3. **优雅停止**: 通过发送 `TerminationSignal` 通知线程停止
4. **队列清理**: 停止时会清理队列中的剩余记录
