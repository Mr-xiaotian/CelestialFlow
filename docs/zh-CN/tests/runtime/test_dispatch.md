# 任务调度核心测试 (test_dispatch.py)

> 📅 最后更新日期: 2026/05/28

## 作用

验证 `celestialflow.runtime.core_dispatch.TaskDispatch` 在 `serial`、`thread`、`async` 三种调度模式下的核心行为：任务执行、异常重试、重复去重和终止信号处理。

## 核心测试对象

- `TaskDispatch`: 负责从任务队列中取出 `TaskEnvelope`，按指定模式分派到 worker 执行，并将结果写入结果队列。

## 关键测试场景

### `TestDispatchSerial` — 串行调度
- 单任务 / 多任务顺序执行
- 重试成功（前 N 次抛异常，最后成功）
- 重试耗尽（始终抛异常，最终无成功结果）
- 终止信号合并（单 ID / 多 ID）

### `TestDispatchThread` — 线程调度
- 10 任务并发（4 worker），验证正确收集结果
- 重复任务去重（同一 hash 投递两次，仅执行一次）

### `TestDispatchAsync` — 异步调度
- 10 任务协程并发（4 worker）
- 异步重试成功（3 次调用后返回正确值）

### `TestDispatchCoreBehavior` — 跨模式参数化
- 空队列 + 终止信号：三种模式均正确退出
- 5 任务结果数：三种模式均输出 5 个结果 + 终止信号

## 运行方式

```bash
# 全部执行
pytest tests/runtime/test_dispatch.py -v

# 仅运行串行调度测试
pytest tests/runtime/test_dispatch.py -k "Serial" -v

# 仅运行线程调度测试
pytest tests/runtime/test_dispatch.py -k "Thread" -v

# 仅运行异步调度测试
pytest tests/runtime/test_dispatch.py -k "Async" -v

# 仅运行跨模式参数化测试
pytest tests/runtime/test_dispatch.py -k "CoreBehavior" -v
```

## 性能参考

| 测试类 | 耗时 |
|--------|------|
| `TestDispatchSerial` | ~0.1s |
| `TestDispatchThread` | ~0.2s |
| `TestDispatchAsync` | ~0.2s |
| `TestDispatchCoreBehavior` | ~0.3s |

## 重要细节

- 测试使用 `TaskEnvelope` 封装任务，通过 `_put` 和 `_put_termination` 辅助函数注入队列。
- 终止信号通过公开 API `task_queue.put(TerminationSignal(...))` 注入，而非直接操作内部 `TerminationIdPool`。
- 异步测试使用 `asyncio.run()` 创建独立事件循环，避免与已有循环冲突。

## 注意事项

- 调度器是 `TaskExecutor` 和 `TaskStage` 的底层执行引擎，其正确性直接影响整个框架的任务执行。
- 相关实现位于 `src/celestialflow/runtime/core_dispatch.py`。
