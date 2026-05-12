# bench_http_grpc.py 基准测试说明

> 📅 最后更新日期: 2026/05/09

## 目标

量化对比 CelestialTree 事件追踪系统在不同传输协议（禁用 / HTTP / gRPC）下的性能开销，帮助用户在高精度追踪和最低延迟之间做出权衡。

## 测试内容

| 场景 | 说明 |
|------|------|
| `bench_no_ctree` | 完全禁用 CelestialTree，作为基线 |
| `bench_http_ctree` | 通过 HTTP 协议向 CelestialTree 上报事件 |
| `bench_grpc_ctree` | 通过 gRPC 协议向 CelestialTree 上报事件 |

- **图结构**：`TaskSplitter → TaskStage` 的简单链
- **任务**：`no_op` 恒等函数（处理 `range(1e4)`）
- **配置**：`stage_mode="thread"`，`execution_mode="thread"`，`max_workers=50`

## 关键配置

- `ctree_host`、`ctree_http_port`、`ctree_grpc_port` 从 `.env` 读取

## 可能出现的问题

1. **CelestialTree 服务未启动**：HTTP/gRPC 场景下若服务端不可用，测试会直接抛出连接异常。
2. **网络延迟主导结果**：由于任务是 `no_op`（几乎零计算），测得的时间差异几乎完全来自事件上报的网络 RTT，无法反映 CPU 密集型场景下的真实比例。
3. **HTTP 连接未复用**：当前实现每次事件上报可能新建 HTTP 连接，若使用连接池（如 `requests.Session`），HTTP 性能会显著提升。
4. **gRPC 冷启动**：gRPC 首次调用需要 TLS/握手协商，可能在短任务中表现为较高延迟。

## 基准结果（实测）

> 环境：Windows，Python 3.10，TaskSplitter → TaskStage 链，处理 `range(1e4)`
> 外部服务：本地 CelestialTree（HTTP + gRPC）

| 场景 | 耗时 | overhead vs 基线 |
|------|------|------------------|
| **no ctree**（基线） | 4.14s | — |
| **http ctree** | 9.46s | +129% |
| **grpc ctree** | 9.25s | +124% |

**关键结论**：
- HTTP 与 gRPC 在该场景下性能几乎持平（差距 < 2%）
- 事件追踪引入约 **2.3x** 的总耗时增长（4.14s → 9.3s）
- 由于任务是 `no_op`（零计算），overhead 比例被放大；在 CPU 密集型任务中，此比例会显著降低
- gRPC 并未表现出明显优势，可能是因为本地网络 RTT 极低，HTTP 连接复用后差距缩小

## 运行方式

```bash
python bench/bench_http_grpc.py
```

## 依赖

- `celestialflow`（`TaskChain`、`TaskSplitter`、`TaskStage`）
- `python-dotenv`
- 外部服务：CelestialTree（HTTP 端口 + gRPC 端口）
