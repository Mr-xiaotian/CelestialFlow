# bench_mpqueue_vs_shared_memory.py 基准测试说明

## 目标

在更复杂的生产者-消费者拓扑（SPSC、MPSC、SPMC）下，对比 `multiprocessing.Queue` 与基于 `shared_memory` 的自定义环形缓冲区性能。为 CelestialFlow 在高吞吐场景下的 IPC 优化提供深度数据。

## 测试内容

| 拓扑 | 生产者 | 消费者 | 说明 |
|------|--------|--------|------|
| SPSC | 1 | 1 | 单生产者单消费者 |
| MPSC | 4 | 1 | 多生产者单消费者 |
| SPMC | 1 | 4 | 单生产者多消费者 |

- **规模**：`COUNT = 100_000`，`REPEAT = 3`
- **SharedMemory 配置**：`SLOT_COUNT = 1024`，每个 slot 大小 = 4B 长度前缀 + payload
- **同步原语**：`Lock`（保护读写索引）、`Semaphore`（空/满槽位计数）

## 关键实现

### SharedMemory Ring 协议
1. **Producer**：`empty_slots.acquire()` → `write_lock` 下写入 payload → `full_slots.release()`
2. **Consumer**：`full_slots.acquire()` → `read_lock` 下读取 payload → `empty_slots.release()`
3. **关键设计**：`full_slots.release()` 在锁外执行，最大化并发度

## 可能出现的问题

1. **SharedMemory 生命周期管理**：`shm.unlink()` 必须在所有进程关闭后才能执行。若某个子进程异常退出未 `shm.close()`，可能导致 `unlink` 失败或内存泄漏。
2. **slot_size 不足**：若 `payload_max_bytes(mode)` 计算不准或实际 payload 超过 `slot_size - 4`，`producer_shm_ring` 会抛出 `RuntimeError`。
3. **MPSC 写入竞争**：虽然 `write_lock` 保护了索引和写入操作，但多个生产者仍串行化写入，SharedMemory 的优势在 MPSC 下可能不如预期。
4. **Windows 共享内存命名**：`SharedMemory(name=shm_name)` 在 Windows 上依赖全局命名空间，若名称冲突（如同时运行多个 benchmark 实例）会导致不可预期行为。

## 运行方式

```bash
python bench/bench_mpqueue_vs_shared_memory.py
```

## 依赖

- `bench_utils.summarize`
