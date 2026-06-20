# Subagent: Concurrency

> 检查方向：线程安全、锁使用、竞态条件、队列生命周期。

## 检查清单

逐文件审查时，按以下清单逐项排查：

### 1. 线程安全
- 多线程共享的可变状态是否有适当的锁保护？
- 是否存在**未加锁的复合操作**（check-then-act）导致 TOCTOU 竞态？
- 原子操作（如 `count += 1`）是否在非线程安全的数据结构上执行？

### 2. 锁使用
- 锁的粒度是否合理？是否存在持有锁期间执行耗时操作（I/O、网络）？
- 是否存在**死锁风险**（多锁获取顺序不一致、嵌套锁）？
- `threading.Lock` vs `threading.RLock` 的选择是否合理？

### 3. 队列操作
- `Queue.put()` / `Queue.get()` 的超时设置是否合理？
- 是否存在队列未消费导致的内存积压？
- 生产者-消费者模型中的停止信号是否可靠传递？

### 4. 线程生命周期
- 线程是否正确启动和 join？
- 守护线程的退出条件是否明确？
- 是否存在"僵尸线程"（启动后无法停止）？

### 5. 异步代码
- `asyncio` 协程中是否有阻塞调用（应使用 `run_in_executor`）？
- 异步上下文管理器（`async with`）和异步迭代器的使用是否正确？

---

## 区域特化提示

| 区域 | 重点关注 |
|------|---------|
| `runtime/` | `TaskDispatch` 的线程池管理、`TaskMetrics` 的计数器锁、`TaskInQueue`/`TaskOutQueue` |
| `stage/` | Executor 在 thread 模式下的线程安全、`dispatch_thread` 的 future 清理 |
| `persistence/` | Spout 守护线程、Inlet 的线程安全写队列 |
| `funnel/` | Spout 线程生命周期、队列背压处理 |
