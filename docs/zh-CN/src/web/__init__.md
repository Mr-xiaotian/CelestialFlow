# Web 模块

> 📅 最后更新日期: 2026/06/22

Web 模块提供了一个交互式的监控和管理界面，基于 FastAPI 与原生 TypeScript 构建，支持任务状态实时可视化、错误追溯、动态任务注入及全局配置管理。

## 模块概述

Web 模块充当了 `TaskReporter` 与最终用户之间的桥梁。它一方面作为 RESTful API Server 接收并缓存来自运行时的状态快照；另一方面提供高性能、低延迟的单页应用 (SPA)，让开发者能够直观地观察图任务的执行流向、性能瓶颈及异常详情。

## 文件说明

### 核心后端组件

1. **core_server.py** (`TaskWebServer`)
   - **作用**: Web 核心服务器，管理数据缓存、版本控制（known_rev）与 API 路由。
   - **关键功能**: 状态聚合、配置持久化、错误分页查询、任务注入中转。

2. **util_error.py**
   - **作用**: 提供错误日志的过滤、归一化与分页逻辑。

3. **util_config.py**
   - **作用**: 负责 `config.json` 的读写，支持配置降级启动。

### 核心前端组件

前端 TypeScript 源文件位于 `web/static/ts/`，编译为 JS 后由 `templates/index.html` 加载：

1. **main.ts** — 全局入口与轮询协调
2. **utils.ts** — 通用工具函数
3. **i18n.ts** — 国际化支持
4. **web_config.ts** — 配置管理逻辑
5. **dashboard_statuses.ts** — 渲染动态节点卡片，展示各阶段实时性能指标与进度条
6. **dashboard_structure.ts** — 基于 Mermaid.js 渲染任务图拓扑结构，支持动态节点着色
7. **dashboard_history.ts** — 维护多指标历史序列，使用 Chart.js 渲染进度折线图
8. **dashboard_summary.ts** — 全局统计看板的渲染与更新
9. **dashboard_analysis.ts** — 拓扑分析信息的展示
10. **errors.ts** — 错误日志的分页展示与深度过滤
11. **injection.ts** — 管理任务手动注入 UI，支持多节点批量注入
12. **layout_editor.ts** — 卡片布局编辑器（依赖 web_config 的 CARD_TEMPLATES/PANEL_SELECTOR_MAP）

## 架构特点

### 客户端历史累积
为了显著降低前后端通信频率，历史趋势数据不再由后端全量推送，而是由前端基于连续的状态快照（Status Snapshot）在浏览器内存中自行累积和维护。

### 增量拉取机制
所有拉取接口（`pull_*`）均支持 `known_rev` 机制。只有当后端数据版本发生变化时才会传输实际 Payload，否则仅返回版本号，极大节省了轮询带宽。

### 配置降级启动
系统设计了健壮的初始化流程：若后端配置加载失败，前端会自动回退到内置的 `DEFAULT_WEB_CONFIG`，保证监控面板在任何情况下都能正常渲染并显示基础数据。

## 使用模式

### 启动服务器
```bash
# 直接运行命令行工具
celestialflow-web --port 5000
```

### 任务注入示例
```python
import requests

# 注入新任务到指定节点（格式：{节点名: [任务列表]}）
requests.post("http://localhost:5000/api/push_injection_tasks", json={
    "Stage_A": [{"id": 1, "data": "payload"}]
})
```

## 使用示例

### 创建和启动 TaskWebServer 的基本示例

```python
from celestialflow import TaskWebServer

# 创建服务器实例
server = TaskWebServer(
    host="127.0.0.1",   # 监听地址
    port=5000,            # 监听端口
    log_level="info",    # 日志级别
)

# 启动服务器（阻塞调用，会一直运行）
server.start_server()
```

启动后浏览器访问 `http://127.0.0.1:5000` 即可看到 Web UI 监控面板。

### 完整的数据上报链路示例

```python
from celestialflow import TaskGraph, TaskStage, TaskWebServer
from celestialflow.persistence import LogInlet
from celestialflow.observability import TaskReporter
import asyncio


async def main():
    # 1. 先启动 Web 服务器（在后台线程中运行）
    server = TaskWebServer(host="127.0.0.1", port=5000, log_level="info")
    # 实际生产环境中 server.start_server() 会阻塞，
    # 此处示意 reporter 与 server 配合的流程

    # 2. 创建任务图
    def process(x: int) -> int:
        return x * 2

    graph = TaskGraph(name="DemoGraph", schedule_mode="eager")
    stage = TaskStage("Processor", process, execution_mode="thread")
    graph.set_stages([stage])

    # 3. 创建并启动 TaskReporter
    log_inlet = LogInlet()
    reporter = TaskReporter(
        host="127.0.0.1",
        port=5000,
        task_graph=graph,
        log_inlet=log_inlet,
    )
    reporter.start()

    # 4. 执行任务
    graph.start_graph({stage.get_name(): range(50)})

    # 5. 停止上报器
    reporter.stop()


asyncio.run(main())
```
