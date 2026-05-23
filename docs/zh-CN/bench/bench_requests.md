# bench_requests.py 基准测试说明

> 📅 最后更新日期: 2026/04/22

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

## 基准结果（实测）

> 环境：Windows，Python 3.10，目标 https://httpbin.org/get，50 请求，10 并发线程

| 场景 | 平均耗时 | 中位数 | 标准差 | 最小值 | 最大值 |
|------|----------|--------|--------|--------|--------|
| **Sequential - no session** | 1144.1 ms | 1059.7 ms | 169.0 ms | 991.9 ms | 1680.1 ms |
| **Sequential - with session** | **274.7 ms** | **166.8 ms** | 204.5 ms | 162.1 ms | 1047.7 ms |
| **Concurrent - no session** | 1795.4 ms | 1738.8 ms | 417.9 ms | 1180.0 ms | 2837.8 ms |
| **Concurrent - per-thread session** | 1734.6 ms | 1738.8 ms | 215.9 ms | 1154.4 ms | 2407.4 ms |

**关键结论**：
- **Session 复用是最大收益来源**：顺序请求下，使用 Session 比无 Session 快 **4.2x**（1144ms → 275ms），因为避免了重复 TCP/TLS 握手
- **并发未带来额外收益**：在本测试中，并发场景（10 线程）的均值反而高于串行，原因是 httpbin 的公网延迟和服务器端处理成为瓶颈，客户端并发无法突破
- **每线程独立 Session 无意义**：在并发场景下，每个线程独立 Session 与无 Session 性能几乎相同，因为连接复用优势被高并发下的连接池竞争抵消
- 对 CelestialFlow 的启示：Reporter 和 CelestialTree HTTP 客户端应全局复用 `requests.Session`

## 运行方式

```bash
python bench/bench_requests.py
```

## 参数调整

### 修改请求数与并发数

在 `bench/bench_requests.py` 顶部修改配置：

```python
NUM_REQUESTS = 10          # 减少请求数，快速验证
# NUM_REQUESTS = 200       # 增加请求数，观察连接池预热后的稳态性能

CONCURRENT_WORKERS = 4     # 减少并发线程
# CONCURRENT_WORKERS = 50  # 高并发场景
```

### 更换测试目标

```python
TEST_URL = "https://httpbin.org/get"             # 默认公网目标
# TEST_URL = "http://localhost:8000/api/health"  # 本地测试服务
```

### 只测试特定场景

```python
if __name__ == "__main__":
    print("\n[1/4] Sequential - no session")
    # test_without_session(...)             # 跳过无 Session 测试

    print("\n[2/4] Sequential - with session")  # 仅测试 Session 复用
    test_with_session(TEST_URL, NUM_REQUESTS)
    # ...
```

修改后运行：

```bash
python bench/bench_requests.py
```

## 依赖

- `requests`
