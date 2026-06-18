# CelestialTree Client

> 📅 最后更新日期: 2026/06/18

CelestialFlow 支持接入 `celestialtree` 客户端，用于实现细粒度的任务全链路追踪（Provenance）和事件记录。

> `celestialtree` 现已从 CelestialFlow 默认运行时依赖中移出。
> 如果你需要本页介绍的追踪能力，请单独安装 `celestialtree`，或者在源码仓库中执行 `uv sync --group dev`。

## 简介

CelestialTree 是一个独立的事件溯源系统。CelestialFlow 通过 `CelestialTreeClient` 将任务生命周期中的关键事件（输入、成功、失败、重试、分裂、路由等）发送给 CelestialTree 服务。

这使得用户可以：
1. **追踪数据血缘**: 查询某个结果是由哪个原始任务、经过哪些步骤生成的。
2. **定位错误根因**: 查询某个错误任务的上游来源。
3. **可视化执行树**: 生成任务执行的调用树。

## 安装

```bash
# 已安装 celestialflow，仅额外补装 CelestialTree
uv pip install celestialtree

# 如果你是在源码仓库中开发/运行 demo
uv sync --group dev
```

## 配置

当前 `TaskGraph.set_ctree()` 接收的是一个事件客户端实例，而不是旧版的 `use_ctree=True` / `host=...` 形式。

在 `TaskGraph` 初始化后配置：

```python
from celestialtree import Client as CelestialTreeClient

ctree_client = CelestialTreeClient(
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
    transport="grpc",
)

graph.set_ctree(ctree_client)
```

## 事件类型

框架会自动发出以下类型的事件：

- `task.input`: 任务进入 Stage。
- `task.success`: 任务处理成功。
- `task.error`: 任务处理失败。
- `task.retry.N`: 任务第 N 次重试。
- `task.split`: 任务分裂。
- `task.route`: 任务路由。
- `task.duplicate`: 重复任务检测。
- `termination.input` / `termination.merge`: 终止信号流转。

## 溯源查询

`TaskGraph` 提供了简化的封装方法来查询溯源信息：

### get_stage_input_trace

获取某个 Stage 当前所有输入任务的溯源树（即这些任务分别来自哪里）。

```python
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
print(trace_str)
```

### get_error_trace

获取特定错误 ID 的溯源树。

```python
trace_str = graph.get_error_trace(error_id=12345)
print(trace_str)
```
