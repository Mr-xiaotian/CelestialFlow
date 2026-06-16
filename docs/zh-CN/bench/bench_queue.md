# bench_queue.py 基准测试说明

> 📅 最后更新日期: 2026/06/16

## 目标

在单进程环境下对比多种队列实现的 put/get/qsize/empty 操作性能，包括线程队列、多进程队列、Manager 队列以及 Redis 队列。

## 测试内容

| 队列类型 | 说明 | 测试操作 |
|----------|------|----------|
| `ThreadQueue` | `queue.Queue` | put, get, qsize, empty |
| `MPQueue` | `multiprocessing.Queue` | put, get, qsize, empty |
| `Manager().Queue` | `Manager().Queue` | put, get, qsize, empty |
| `Redis List` | Redis `lpush`/`rpop` | lpush, rpop, llen, empty-check |
| `Redis Stream` | Redis `xadd`/`xread` | xadd, xread, xlen, empty-check |

- **规模**：`COUNT = 100_000`
- **Redis 配置**：从 `.env` 读取（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 可能出现的问题

1. **`MPQueue` 在单进程中的误导性**：`MPQueue` 设计用于跨进程，在单进程内测试时底层管道/套接字开销会被放大，结果不代表真实跨进程性能。
2. **Redis Stream 的 block 行为**：`xread` 使用 `block=0`（无限阻塞），若消息数与预期不符，测试会永远挂死。
3. **`qsize()` 的不可靠性**：`MPQueue.qsize()` 在多进程环境下是非精确的；即使在单进程测试中，其值也可能因内部缓冲而滞后。
4. **Redis `flushdb`**：测试开始前会执行 `flushdb`，若连接到生产 Redis 实例，将导致数据丢失。

## 基准结果（实测）

### 历史结果 - Windows 本地队列与 Redis（时间未记录）

> 环境：Windows，Python 3.10，COUNT=100,000
> 注：Redis 测试因本地 Redis 服务响应缓慢，在 120s 超时内未完成，以下为本地队列实测结果。

#### 本地队列对比

| 队列类型 | put/lpush | get/rpop | 备注 |
|----------|-----------|----------|------|
| **ThreadQueue** | 0.0777s | 0.0723s | 纯内存，无序列化，最快 |
| **MPQueue** | 0.1198s | **3.0071s** | put 尚可，get 因跨进程反序列化极慢 |
| **Manager().Queue** | 8.0674s | 8.5525s | Manager 服务器转发，慢 100x+ |

#### Redis 队列（历史参考值，本次未完整跑完）

| 操作 | 预估耗时（100k） | 瓶颈 |
|------|-----------------|------|
| Redis List lpush/rpop | ~2-3s | 网络 RTT |
| Redis Stream xadd/xread | ~3-5s | 流解析开销 |

**关键结论**：
- ThreadQueue 比 MPQueue get 快 **40x**，比 Manager().Queue 快 **100x+**
- MPQueue 的 get 是最大短板（3s vs 0.07s），若框架内部队列可退化为线程模式，收益巨大
- Redis 队列适合跨设备/跨网络场景，本地 IPC 完全不应考虑

### 2026/06/16 - 本地队列与 Redis 复测

> 环境：Windows，COUNT=100,000，本轮 Redis 服务可用并完成了 List / Stream 测试

#### 本地队列对比

| 队列类型 | put/lpush | get/rpop | qsize/xlen/llen | empty |
|----------|-----------|----------|-----------------|-------|
| **ThreadQueue** | 0.0401s | 0.0427s | 0.0159s | 0.0202s |
| **MPQueue** | 0.0857s | 1.7550s | 0.0650s | 0.9309s |
| **Manager().Queue** | 3.4102s | 3.2287s | 3.1512s | 3.0891s |

#### Redis 队列（本轮实测）

| 类型 | 写入 | 读取 | 长度查询 | empty |
|------|------|------|----------|-------|
| Redis List | 24.7174s | 24.8115s | 24.7813s | 24.5446s |
| Redis Stream | 26.5111s | 0.5551s | 25.8857s | 27.2085s |

**本轮补充结论**：
- 本地队列仍然远快于 Redis；`ThreadQueue` 依旧是纯本机场景下最轻的选择
- `MPQueue` 的 `get` 和 `empty` 成本依旧很高，跨进程同步状态检查尤其昂贵
- 本轮 Redis 服务可用后可以看到：`xread` 很快，但 `xadd` / `xlen` / 清空阶段都非常重，整体不适合本地高频队列

## 运行方式

```bash
python bench/bench_queue.py
```

## 参数调整

### 修改测试规模

脚本默认 `COUNT = 100_000`，可在 `if __name__ == "__main__"` 中修改：

```python
if __name__ == "__main__":
    COUNT = 10_000       # 小规模快速验证（耗时数秒）
    # COUNT = 1_000_000  # 大规模压测（注意 Manager().Queue 会极慢）
```

### 只测试特定队列类型

```python
if __name__ == "__main__":
    COUNT = 10_000

    # test_threadqueue_perf(COUNT)        # 注释掉线程队列
    test_mpqueue_perf(COUNT)              # 仅测试 MPQueue
    # test_manager_queue_perf(COUNT)      # 跳过 Manager 队列
    # test_redis_list_perf(COUNT)         # 跳过 Redis
    # test_redis_stream_perf(COUNT)
```

修改后运行：

```bash
python bench/bench_queue.py
```

## 依赖

- `redis`
- `python-dotenv`
