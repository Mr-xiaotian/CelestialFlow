# bench_datastructures.py 基准测试说明

## 目标

对比多种 Python 数据结构及外部存储在单线程/多进程环境下的读写性能，为 CelestialFlow 选择内部队列、共享状态和持久化后端提供量化依据。

## 测试内容

| 测试项 | 说明 | 规模 |
|--------|------|------|
| `test_builtin_dict` | 原生字典 put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` 单线程读写 | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` 跨进程读写 | N=10,000 |
| `test_manager_dict` | `Manager().dict` 跨进程读写 | N=10,000 |
| `test_value_number` | `multiprocessing.Value` 原子自增 | N=10,000 |
| `test_redis_plain` | Redis 逐条 set/get | N=10,000 |
| `test_redis_pipeline` | Redis Pipeline 批量 set/get | N=10,000 |
| `test_redis_multithread_plain` | Redis 多线程并发写入 | N=10,000 / 10 threads |
| `test_redis_hash` | Redis Hash 逐条 hset/hget | N=10,000 |
| `test_redis_list` | Redis List 逐条 rpush/lindex | N=10,000 |
| `test_redis_set` | Redis Set 逐条 sadd/sismember | N=10,000 |
| `test_redis_zset` | Redis Sorted Set 逐条 zadd/zscore | N=10,000 |

## 关键配置

- `N = 10000`：每个测试的迭代次数
- Redis 连接参数从 `.env` 加载（`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`）

## 可能出现的问题

1. **Redis 连接失败**：若 `.env` 中 Redis 配置缺失或服务未启动，Redis 相关测试会被跳过，仅输出警告。
2. **Windows 多进程启动开销**：`MPQueue` 和 `Manager().dict` 测试在 Windows `spawn` 模式下，子进程启动本身可能占去大量时间，导致测得的 put/get 时间不准确。
3. **MPQueue 的缓冲区限制**：`mpqueue_worker` 中先 put 全部 N 个元素再 get，当 N 很大时可能触发的 OS 管道缓冲区上限（尤其在 Linux 上）。

## 运行方式

```bash
python bench/bench_datastructures.py
```

## 依赖

- `redis`
- `python-dotenv`
