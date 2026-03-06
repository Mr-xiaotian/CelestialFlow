# RuntimeFactories

`runtime/factories.py` 提供运行时对象工厂。

## 主要函数

- `make_counter(mode, ...)`：按执行模式构造计数器。
- `make_queue_backend(mode)`：按执行模式选择队列实现。
- `make_taskqueue(mode, direction, stage)`：构造 `TaskQueue` 实例。

## 设计目标

- 统一 serial/thread/process/async 的底层资源创建逻辑。
