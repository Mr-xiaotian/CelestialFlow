# Persistence Base

`persistence/core_funnel.py` 提供了日志和错误持久化的基础类，是 `LogSpout`/`LogInlet` 和 `FailSpout`/`FailInlet` 的父类。

## 设计目的

任务执行过程中产生的日志和错误需要持久化存储。基础类提供了：
- 多进程安全的队列通信
- 后台线程监听
- 优雅的启动和停止机制

## BaseSpout

出口基类，在后台线程中接收并处理记录。

### 初始化

```python
class BaseSpout:
    def __init__(self):
        self.queue = MPQueue()  # 多进程安全队列
        self._thread: Thread | None = None
```

### 核心方法

#### start

启动监听线程。

```python
def start(self):
    """启动后台监听线程。"""
```

流程：
1. 调用 `_before_start()` 钩子
2. 创建并启动后台线程
3. 线程执行 `_listen()` 方法

#### stop

停止监听线程。

```python
def stop(self):
    """停止监听线程并清理资源。"""
```

流程：
1. 发送终止信号到队列
2. 等待线程结束
3. 清理队列资源
4. 调用 `_after_stop()` 钩子

#### get_queue

获取队列对象。

```python
def get_queue(self) -> MPQueue:
    """返回队列对象，供生产者使用。"""
```

### 可重写方法

```python
def _before_start(self):
    """启动前的初始化操作。"""
    return None

def _handle_record(self, record):
    """处理单条记录（必须重写）。"""
    raise NotImplementedError

def _after_stop(self):
    """停止后的清理操作。"""
    return None
```

### 内部实现

```python
def _listen(self):
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

---

## BaseInlet

收集器基类，将记录发送到队列。

### 初始化

```python
class BaseInlet:
    def __init__(self, queue):
        self.queue: MPQueue = queue
```

### 核心方法

```python
def _funnel(self, record):
    """将记录放入队列。"""
    self.queue.put(record)
```

---

## 使用示例

### 创建自定义出口

```python
from celestialflow.persistence.core_funnel import BaseSpout, BaseInlet
import json

class JsonSpout(BaseSpout):
    """将记录保存为 JSON 文件。"""

    def _before_start(self):
        self.file = open("output.jsonl", "a")

    def _handle_record(self, record):
        self.file.write(json.dumps(record) + "\n")
        self.file.flush()

    def _after_stop(self):
        self.file.close()

class JsonInlet(BaseInlet):
    """发送记录到 JsonSpout。"""

    def log(self, data):
        self._funnel(data)
```

### 在执行器中使用

```python
from celestialflow import TaskExecutor

# 创建出口
listener = JsonSpout()
listener.start()

# 创建收集器
sinker = JsonInlet(listener.get_queue())

# 配置执行器
executor = TaskExecutor(func=process)
executor.init_sinker(fail_queue=listener.get_queue(), log_queue=listener.get_queue())

# 运行
executor.start(range(100))

# 停止
listener.stop()
```

---

## 继承关系

```
BaseSpout
├── LogSpout (persistence/core_log.py)
└── FailSpout (persistence/core_fail.py)

BaseInlet
├── LogInlet (persistence/core_log.py)
└── FailInlet (persistence/core_fail.py)
```

## 注意事项

1. **多进程安全**: 使用 `multiprocessing.Queue` 确保跨进程通信安全
2. **守护线程**: 监听线程设置为守护线程，主进程退出时自动结束
3. **优雅停止**: 通过发送 `TerminationSignal` 通知线程停止
4. **队列清理**: 停止时会清理队列中的剩余记录