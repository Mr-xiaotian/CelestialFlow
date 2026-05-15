# demo_stages.py 演示说明

> 📅 最后更新日期: 2026/05/15

## 目标

演示 CelestialFlow 中特殊 Stage 节点的使用：`TaskSplitter`（任务拆分）、`TaskRouter`（任务路由）、`TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource`（Redis 分布式传输）。构建包含循环依赖和跨设备协作的复杂任务图。

## 自定义子类

- `DownloadRedisTransport`：继承 `TaskRedisTransport`，重写 `get_args` 方法将 `/tmp/` 路径替换为 `X:/Download/download_go/`（供 Go Worker 使用）。
- `DownloadStage`：继承 `TaskStage`，重写 `get_args` 方法将 `/tmp/` 路径替换为 `X:/Download/download_py/`（供 Python 本地下载使用）。

## 演示场景

### `demo_splitter_0`
模拟爬虫工作流：
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
- `demo_redis_ack_0`：斐波那契（CPU 密集）
- `demo_redis_ack_1`：`sum_int`（通信开销主导）
- `demo_redis_ack_2`：图片下载（I/O 密集）

### `demo_redis_source_0`
演示 `TaskRedisSource` 从 Redis 独立读取任务，实现跨设备/跨 TaskGraph 的数据传输。

### `demo_router_0`
演示 `TaskRouter` 根据奇偶性将任务分发到不同下游节点。

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
# 单独运行某个演示
python demo/demo_stages.py
```

## 依赖

- `celestialflow`（`TaskGraph`、`TaskStage`、`TaskChain`、`TaskSplitter`、`TaskRouter`、`TaskRedisTransport`、`TaskRedisAck`、`TaskRedisSource`）
- `demo_utils`
- `python-dotenv`
- 外部服务：Redis、CelestialTree（可选）、Reporter（可选）、Go Worker（可选）
