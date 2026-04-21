# bench_queue.py 基准测试说明

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

## 运行方式

```bash
python bench/bench_queue.py
```

## 依赖

- `redis`
- `python-dotenv`
