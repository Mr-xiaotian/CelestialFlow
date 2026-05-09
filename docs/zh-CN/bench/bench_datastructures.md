# bench_datastructures.py 基准测试说明

> 📅 最后更新日期: 2026/05/09

## 目标

对比多种 Python 数据结构及外部存储在单线程环境下的读写性能，为 CelestialFlow 选择内部队列和持久化后端提供量化依据。

## 测试内容

| 测试项 | 说明 | 规模 |
|--------|------|------|
| `test_builtin_dict` | 原生字典 put/get | N=10,000 |
| `test_queue_thread` | `queue.Queue` 单线程读写 | N=10,000 |
| `test_mpqueue` | `multiprocessing.Queue` 跨进程读写（已废弃，仅保留供参考） | N=10,000 |
| `test_manager_dict` | `Manager().dict` 跨进程读写 | N=10,000 |
| `test_value_number` | `multiprocessing.Value` 原子自增（已废弃，仅保留供参考） | N=10,000 |
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
2. **MPQueue 的缓冲区限制**：`mpqueue_worker` 中先 put 全部 N 个元素再 get，当 N 很大时可能触发的 OS 管道缓冲区上限（尤其在 Linux 上）。

> **注意**：`test_mpqueue` 和 `test_value_number` 使用的 `multiprocessing.Queue` 和 `multiprocessing.Value` 已不再被框架内部使用（`stage_mode="process"` 已移除），这些基准测试仅作为历史参考保留。

## 运行方式

```bash
python bench/bench_datastructures.py
```

## 基准结果（实测）

> 环境：Windows，Python 3.10，本地 Redis，N=10,000

| 测试项 | put/set | get | 备注 |
|--------|---------|-----|------|
| Built-in dict | 0.0008s | 0.0003s | 单线程基准，最快 |
| Queue (thread) | 0.0101s | 0.0108s | 线程安全队列 |
| MPQueue | 0.0149s | 0.3072s | 跨进程队列，get 因序列化显著变慢 |
| Manager.dict | 0.5156s | 0.5369s | Manager 服务器转发，慢 50-100x |
| Value (number) | 0.0174s | — | 10,000 次原子自增 |
| Redis plain | 2.8352s | 2.9026s | 逐条 RTT，网络延迟主导 |
| Redis pipeline | 0.1474s | 0.1202s | 批量打包，比 plain 快 ~20x |
| Redis multi-thread | 1.1749s | 1.0765s | 10 线程并发，无 pipeline |
| Redis hash | 2.8391s | 2.7675s | hset/hget，与 plain 持平 |
| Redis list | 2.6853s | 2.8370s | rpush/lindex |
| Redis set | 2.7932s | 3.2969s | sadd/sismember |
| Redis zset | 3.1955s | 3.1854s | zadd/zscore |

**关键结论**：
- 纯内存结构（dict、thread Queue）比任何 IPC/网络方案快 2-3 个数量级
- Redis Pipeline 是网络场景下的必选项，可将延迟从 ~2.8s 降至 ~0.15s
- MPQueue 的 get 比 put 慢约 20x，主要受 pickle 反序列化拖累

## 依赖

- `redis`
- `python-dotenv`
