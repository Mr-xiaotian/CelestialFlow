# CelestialTree Client

CelestialFlow 集成了 `celestialtree` 客户端，用于实现细粒度的任务全链路追踪（Provenance）和事件记录。

## 简介

CelestialTree 是一个独立的事件溯源系统。CelestialFlow 通过 `CelestialTreeClient` 将任务生命周期中的关键事件（输入、成功、失败、重试、分裂、路由等）发送给 CelestialTree 服务。

这使得用户可以：
1. **追踪数据血缘**: 查询某个结果是由哪个原始任务、经过哪些步骤生成的。
2. **定位错误根因**: 查询某个错误任务的上游来源。
3. **可视化执行树**: 生成任务执行的调用树。

## 配置

在 `TaskGraph` 初始化时配置：

```python
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)
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
trace_str = graph.get_error_trace(error_id="...")
print(trace_str)
```
