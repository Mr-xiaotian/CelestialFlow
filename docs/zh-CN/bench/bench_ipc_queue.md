# bench_ipc_queue.py 基准测试说明

> 📅 最后更新日期: 2026/04/22

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

## 基准结果（实测）

> 环境：Windows，Python 3.10，spawn 模式，COUNT=100,000，REPEAT=3，负载=int（8 字节）

| 机制 | 平均耗时 | 吞吐量 | 相对 MPQueue |
|------|----------|--------|-------------|
| **MPQueue** | 1.328s | 75,277 items/s | 1.00x |
| **SimpleQueue** | 1.099s | 90,962 items/s | 1.21x |
| **Pipe** | 1.006s | 99,358 items/s | 1.32x |
| **Manager().Queue** | 7.884s | 12,684 items/s | 0.17x |

**关键结论**：
- **Pipe 最快**：比 MPQueue 快 32%，且无需队列抽象层
- **SimpleQueue 次之**：无锁实现，比 MPQueue 快 21%，但仅支持单生产者单消费者
- **Manager().Queue 最慢**：仅为 MPQueue 的 17% 吞吐量，Manager 服务器进程成为绝对瓶颈
- 在 CelestialFlow 的多进程队列选型中，Pipe 和 SimpleQueue 是高吞吐场景的最优解（若拓扑允许）

## 运行方式

```bash
python bench/bench_ipc_queue.py
```

## 参数调整

### 修改测试规模与负载模式

在 `bench/bench_ipc_queue.py` 顶部调整全局配置：

```python
COUNT = 10_000       # 减少次数，快速验证
# COUNT = 1_000_000  # 大规模压测

REPEAT = 1           # 只跑 1 轮，快速验证
# REPEAT = 5         # 增加轮次，提高统计可信度

PAYLOAD_MODE = "small"  # 可选：int / small / medium / large
```

### 只测试特定 IPC 机制

在 `main()` 中可选择性运行：

```python
def main() -> None:
    # run_queue_case(name="MPQueue", ...)   # 注释掉 MPQueue
    # run_queue_case(name="SimpleQueue", ...)
    run_queue_case(name="Pipe", ...)          # 仅测试 Pipe
    # run_queue_case(name="Manager().Queue", ...)
```

修改后运行：

```bash
python bench/bench_ipc_queue.py
```

## 依赖

- `bench_utils.summarize`
