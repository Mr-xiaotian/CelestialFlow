# TaskWeb

TaskWeb 模块提供了一个基于 FastAPI 的轻量级 Web 服务器，用于实时监控和管理任务图的运行。

## 启动方式

可以通过命令行直接启动：

```bash
# 默认监听 0.0.0.0:5000
python -m celestialflow.task_web

# 指定端口
python -m celestialflow.task_web --port 5005
```

或者在代码中启动（通常不需要，因为 `TaskGraph` 会连接到一个独立运行的 Web 服务）。

## 功能界面

访问 `http://localhost:5000` (或指定端口) 可看到 Web UI。

主要包含以下面板：
1. **Dashboard**: 任务图的实时状态概览（节点数、成功/失败/积压任务数）。
2. **Structure**: 任务图的结构可视化。
3. **Errors**: 实时错误日志列表。
4. **Topology**: 拓扑关系图。

## API 接口

TaskWeb 提供了一系列 RESTful API 供 `TaskReporter` 调用和前端使用。

### 接收数据 (Pull)

- `GET /api/get_structure`: 获取图结构。
- `GET /api/get_status`: 获取节点运行状态。
- `GET /api/get_errors`: 获取错误日志。
- `GET /api/get_topology`: 获取拓扑数据。
- `GET /api/get_summary`: 获取概要统计。
- `GET /api/get_task_injection`: 获取待注入的任务（供 TaskGraph 拉取）。

### 推送数据 (Push)

- `POST /api/push_structure`
- `POST /api/push_status`
- `POST /api/push_errors_meta` / `push_errors_content`
- `POST /api/push_topology`
- `POST /api/push_summary`
- `POST /api/push_injection_tasks`: 前端注入任务到此接口，随后被 TaskGraph 拉取。
