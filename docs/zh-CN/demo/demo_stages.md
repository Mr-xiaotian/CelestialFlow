# demo_stages.py 演示说明

> 📅 最后更新日期: 2026/05/24

## 目标

演示 CelestialFlow 中特殊 Stage 节点的使用：`TaskSplitter`（任务拆分）、`TaskRouter`（任务路由）、`TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource`（Redis 分布式传输）。构建包含循环依赖和跨设备协作的复杂任务图。

## 自定义子类

- `DownloadRedisTransport`：继承 `TaskRedisTransport`，重写 `get_args` 方法将 `/tmp/` 路径替换为 `X:/Download/download_go/`（供 Go Worker 使用）。
- `DownloadStage`：继承 `TaskStage`，重写 `get_args` 方法将 `/tmp/` 路径替换为 `X:/Download/download_py/`（供 Python 本地下载使用）。

## 演示场景

### `demo_splitter_0`
模拟爬虫工作流：

```mermaid
flowchart TD
    GenURLs["GenURLs<br/>生成 URL 列表"] -->|直接输出| Logger["Logger<br/>记录爬取信息"]
    GenURLs -->|直接输出| Splitter["Splitter<br/>将 URL 列表拆分为单条"]
    Splitter -->|单个 URL| Downloader["Downloader<br/>下载资源"]
    Splitter -->|单个 URL| Parser["Parser<br/>解析新 URL"]
    Parser -.->|回环| GenURLs
```

- `GenURLs` → 生成 URL 列表
- `Logger` → 记录爬取信息
- `Splitter` → 将 URL 列表拆分为单个 URL
- `Downloader` → 下载资源
- `Parser` → 解析新 URL 并回环到 `GenURLs`

**图结构**：含环图（`parse_stage → generate_stage`）

### `demo_splitter_1`
演示大数据包拆分：输入 `range(int(1e5))` 被包装在列表中传入 `TaskSplitter`，下游逐个接收处理，避免一次性加载过多任务到内存。

### `demo_redis_ack_0/1/2`
对比 Python 本地计算与通过 Redis + Go Worker 外部计算的耗时差异：

```mermaid
flowchart TB
    subgraph Python["Python 本地计算"]
        direction LR
        Start["Start<br/>sleep_1"] -->|直接下发| Compute["计算节点<br/>Fibonacci / Sum / Download"]
        Compute --> Ack["RedisAck<br/>结果确认"]
    end

    subgraph GoWorker["Redis + Go Worker 外部计算"]
        direction LR
        StartGo["Start<br/>sleep_1"] -->|写入| Transport["RedisTransport<br/>key: input"]
        Transport -.->|Go Worker 消费| GoCalc["Go Worker<br/>外部计算"]
        GoCalc -.->|Go Worker 写入| GoAck["RedisAck<br/>key: output"]
    end

    PythonStart["Start"] --> Python
    PythonStart --> GoWorker
```

| 场景 | 计算类型 | Python 本地节点 | Go Worker 节点 |
|------|---------|----------------|----------------|
| `demo_redis_ack_0` | CPU 密集 | `Fibonacci` | 斐波那契计算 |
| `demo_redis_ack_1` | 通信开销主导 | `Sum`（`sum_int`） | 求和计算 |
| `demo_redis_ack_2` | I/O 密集 | `Download`（`download_to_file`，路径 `download_py/`） | 下载图片（`download_go/`） |

> 图中虚线箭头表示跨进程/跨设备的数据流转。所有 `demo_redis_ack_*` 的 Python 路径和 Go Worker 路径共享同一个 `Start` 节点：`graph.connect([start_stage], [redis_tranport, compute_stage])`。

### `demo_redis_source_0`
演示 `TaskRedisSource` 从 Redis 独立读取任务，实现跨设备/跨 TaskGraph 的数据传输。

### `demo_router_0`
演示 `TaskRouter` 根据奇偶性将任务分发到不同下游节点。

```mermaid
flowchart LR
    Origin["Origin<br/>RouterWrapper"] -->|"(target, n)"| Router["Router<br/>stage_mode=serial"]
    Router -->|偶数 n % 2 == 0| StageA["StageA<br/>thread | 2 workers"]
    Router -->|奇数 n % 2 != 0| StageB["StageB<br/>thread | 2 workers"]
```

路由逻辑：`Origin` 阶段的 `RouterWrapper` 根据输入 `n` 的奇偶性生成 `(target, n)` 元组，`Router` 根据 `target` 字段将任务分发到 `StageA`（偶数）或 `StageB`（奇数）。

## 关键配置

- 所有 stage 默认 `stage_mode="thread"`（多线程）
- `set_reporter(True)` 启用监控上报
- `set_ctree(True)` 启用事件追踪

## 可能出现的问题

1. **Redis 依赖**：`demo_redis_*` 系列需要可用的 Redis 服务（`.env` 配置 `REDIS_HOST`、`REDIS_PASSWORD`）。
2. **Go Worker 前期设置**：使用外部 Worker 前需完成 [前期设置](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期设置)。
3. **网络路径硬编码**：`DownloadStage` 和 `DownloadRedisTransport` 中有 Windows 路径硬编码（`X:/Download/...`），在非 Windows 环境或路径不存在时会失败。
4. **长耗时**：`demo_splitter_0` 中各阶段含 4-6 秒随机 sleep，完整执行可能超过 1 分钟。
5. **无断言**：演示脚本，不验证结果正确性。

## 运行方式

```bash
# 运行默认演示（demo_splitter_0）
python demo/demo_stages.py

# 修改 main() 后可运行其他场景
# 如将 demo_splitter_0() 替换为 demo_router_0()
```

## 预期行为

### `demo_splitter_0`（爬虫工作流）

生成 URL 后经 Splitter 拆分，Downloader 和 Parser 并行处理，Parser 结果回环到 Generator：

```
[GenURLs] Generated 3 URLs
[Splitter] Splitting 3 URLs...
[Downloader] Downloading url_0...
[Parser] Parsing url_0...
[Logger] Logging: url_0
[Downloader] Downloading url_1...
...
```

> 含随机 sleep（4-6 秒），总执行时间可能超过 1 分钟。

### `demo_router_0`（奇偶路由）

Origin 根据输入奇偶性生成 `(target, n)`，Router 分发到 StageA（偶数）或 StageB（奇数）：

```
[Origin] Input: 0 -> RouterWrapper(0) -> ('stage_a', 0)
[Origin] Input: 1 -> RouterWrapper(1) -> ('stage_b', 1)
[Router] Routing 0 to stage_a
[Router] Routing 1 to stage_b
[StageA] Received: 0
[StageB] Received: 1
...
```

### `demo_redis_ack_0/1/2`（Redis 分布式计算）

Python 本地计算与 Go Worker 外部计算并行执行，结果分别写入 Redis Ack：

```
[Fibonacci] Computing fibonacci for n=10...
[RedisTransport] Writing 10 to Redis key 'input:0'
[RedisAck] Acknowledging fibonacci result: 55
...
```

> 需要提前启动 Redis 和 Go Worker（参见[前期设置]）。不会自动停止，需手动 Ctrl+C 终止。

### `demo_splitter_1`（大数据拆分）

将 `range(100000)` 包装成列表传入 Splitter，逐个输出给下游处理，无额外输出日志。

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`TaskChain`、`TaskSplitter`、`TaskRouter`、`TaskRedisTransport`、`TaskRedisAck`、`TaskRedisSource`）
- `demo_utils`
- `python-dotenv`
- 外部服务：Redis、CelestialTree（可选）、Reporter（可选）、Go Worker（可选）
