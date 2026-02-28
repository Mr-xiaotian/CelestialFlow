# TaskReporter

`TaskReporter` 是一个后台组件，负责收集任务图的运行状态并上报给远程 Web 服务器（CelestialFlow Web UI）。同时也负责从服务器拉取控制指令（如任务注入）。

## 功能特性

- **状态上报**: 周期性推送任务图的结构、拓扑、运行状态（计数器）、错误信息等。
- **任务注入**: 从 Web UI 接收用户注入的新任务，并动态插入到运行中的任务图中。
- **参数动态调整**: 支持从服务器拉取配置（如上报间隔）。
- **错误日志同步**: 支持增量推送错误日志。

## 使用方式

通常不需要直接实例化，而是通过 `TaskGraph` 启用：

```python
graph = TaskGraph(...)
# 开启 Reporter，连接到本地 5005 端口
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

## API 交互

Reporter 会与以下 Web API 交互：

- `GET /api/get_interval`: 获取上报间隔。
- `GET /api/get_task_injection`: 获取注入的任务。
- `POST /api/push_status`: 推送运行时状态快照。
- `POST /api/push_structure`: 推送图结构信息。
- `POST /api/push_topology`: 推送拓扑连接信息。
- `POST /api/push_summary`: 推送图概要。
- `POST /api/push_errors_meta` / `push_errors_content`: 推送错误信息。
