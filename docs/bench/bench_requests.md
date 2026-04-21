# bench_requests.py 基准测试说明

## 目标

量化对比 `requests` 库在不同使用模式下的 HTTP 请求性能：是否使用 Session、是否并发、Session 的共享粒度。为 CelestialFlow 中涉及 HTTP 通信的模块（Reporter、CelestialTree HTTP 客户端）提供优化依据。

## 测试内容

| 场景 | Session 使用方式 | 并发 |
|------|-----------------|------|
| Sequential - no session | 每次新建 `requests.get()` | 无 |
| Sequential - with session | 复用单个 `Session` | 无 |
| Concurrent - no session | 每次新建 `requests.get()` | 10 线程 |
| Concurrent - per-thread session | 每个线程独立 `Session` | 10 线程 |

- **目标 URL**：`https://httpbin.org/get`
- **请求数**：`NUM_REQUESTS = 50`
- **超时**：`TIMEOUT = 30`

## 关键指标

输出每组请求的 mean、median、stdev、min、max（毫秒）。

## 可能出现的问题

1. **网络波动**：目标 `httpbin.org` 位于公网，延迟受本地网络和国际链路质量影响，单次结果不具备可重复性。
2. **连接池未预热**：`requests.Session` 的连接池在首次请求时建立 TCP/TLS 连接，前几个请求的耗时可能显著高于后续请求。
3. **GIL 限制**：`ThreadPoolExecutor` 中的线程受 Python GIL 约束，`requests` 的 CPU 密集部分（如 TLS 握手、JSON 解析）无法真正并行。
4. **httpbin 速率限制**：频繁测试可能触发 httpbin 的限流，返回 429 或连接重置。

## 运行方式

```bash
python bench/bench_requests.py
```

## 依赖

- `requests`
