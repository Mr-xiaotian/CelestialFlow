# TaskTypes

TaskTypes 模块定义了框架中使用的基础数据类型、枚举和辅助类。

## StageStatus

枚举类，表示 `TaskStage` 的运行状态。

- `NOT_STARTED` (0): 未启动
- `RUNNING` (1): 运行中
- `STOPPED` (2): 已停止

## TaskEnvelope

任务数据的包装类，在各个 Stage 之间传递。它封装了原始任务数据、任务哈希和任务 ID。

```python
class TaskEnvelope:
    def __init__(self, task, hash, id):
        self.task = task  # 原始任务数据
        self.hash = hash  # 任务内容的哈希值
        self.id = id      # 任务唯一 ID
```

## TerminationSignal

用于标记任务队列终止的哨兵对象。当 Stage 接收到此信号时，表示上游已无更多任务，应当准备停止。

```python
TERMINATION_SIGNAL = TerminationSignal()
```

## ValueWrapper & SumCounter

用于多线程/多进程环境下的计数器封装。

- `ValueWrapper`: 简单的值包装器，可选配锁。
- `SumCounter`: 聚合多个计数器（支持 thread/process 模式），用于统计任务处理总数。

## Exceptions

- `UnconsumedError`: 标记任务未被消费的异常。
