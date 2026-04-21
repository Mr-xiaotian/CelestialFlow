# bench_ipc_queue.py 基准测试说明

## 目标

在真实跨进程场景下对比多种 Python IPC（进程间通信）机制的性能：MPQueue、SimpleQueue、Pipe、Manager().Queue。为 CelestialFlow 在多进程模式下的队列选型提供数据支持。

## 测试内容

| 机制 | 说明 | 拓扑支持 |
|------|------|----------|
| `MPQueue` | 标准多进程队列 | SPSC |
| `SimpleQueue` | 无锁简化队列 | SPSC |
| `Pipe` | 双向/单向管道 | SPSC |
| `Manager().Queue` | 基于 Manager 服务器的队列 | SPSC |

- **规模**：`COUNT = 100_000`，`REPEAT = 3`
- **负载模式**：`int`（8 字节）、`small`（~16 字节）、`medium`（~144 字节）、`large`（~4104 字节）
- **校验**：通过 checksum 验证数据完整性（无丢失、无损坏）

## 关键实现

- `producer_queue` / `consumer_queue`：使用哨兵对象 `_SENTINEL = None` 标识流结束
- `producer_pipe` / `consumer_pipe`：显式 `conn.close()` 防止句柄泄漏
- `expected_checksum`：根据负载模式解析计算预期校验和

## 可能出现的问题

1. **Pipe 句柄泄漏**：若 consumer/producer 未正确关闭连接，Windows 上可能导致子进程无法退出或句柄耗尽。
2. **`Manager().Queue` 的 server 瓶颈**：所有数据必须经过 Manager 服务器进程转发，当生产者/消费者并发高时，server 进程成为单点瓶颈。
3. **大负载内存复制**：`large` 模式下每个 payload 约 4KB，100k 次传输意味着约 400MB 的数据复制，主要测的是内存带宽而非队列本身。
4. **Windows `spawn` 序列化开销**：所有 payload 必须通过 pickle 在父子进程间传输，大对象序列化/反序列化时间会占主导。

## 运行方式

```bash
python bench/bench_ipc_queue.py
```

## 依赖

- `bench_utils.summarize`
