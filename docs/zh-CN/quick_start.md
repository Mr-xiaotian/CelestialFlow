# 快速开始（Quick Start）

> 📅 最后更新日期: 2026/06/18

本节将引导你快速安装并运行 **TaskGraph**，通过示例体验其任务图调度机制。

## 创建独立虚拟环境

建议在独立环境中使用，以避免与其他项目依赖冲突。

```bash
# 创建项目虚拟环境（默认生成 .venv）
uv venv --python 3.10

# 激活环境（Windows）
. .\.venv\Scripts\Activate.ps1

# 激活环境（Linux/macOS）
source .venv/bin/activate
```

建议在独立虚拟环境中使用。CelestialFlow 推荐使用 `uv` 管理依赖与环境。

## 安装 CelestialFlow

CelestialFlow 已发布至 [PyPI](https://pypi.org/project/celestialflow/)，可以直接通过 `pip` / `uv pip` 安装，无需克隆源码。

```bash
# 直接安装最新版
uv pip install celestialflow
```

上面的安装只包含 CelestialFlow 默认运行时依赖，不包含 `celestialtree` 这类可选追踪组件。

如果你需要启用 CelestialTree 事件追踪，可以额外执行：

```bash
uv pip install celestialtree
```

不过如果你想要运行之后的测试代码，亦或者想使用基于 Go 语言的 `go_worker` 程序，那么还是需要 clone 项目：

```bash
# 克隆项目
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
uv sync --group dev
```

其中 `dev` 依赖组已经包含 `pytest`、`python-dotenv`、`redis`、`celestialtree` 等开发与扩展所需依赖。

## （可选）设置.env && 启动 Web 可视化

Web监视界面并不是必须的，但可以通过网页获得任务运行的更多信息，推荐使用。

首先，在项目根目录下创建一个 `.env` 文件，并填入以下内容：

```env
# .env
# TaskWeb的监听地址
REPORT_HOST=127.0.0.1
# TaskWeb的监听端口
REPORT_PORT=5005
```

之后，你可以通过以下命令启动Web服务：

```bash
# 如果你pip了项目，可以在当前虚拟环境下可以直接使用命令celestialflow-web
celestialflow-web --port 5005

# 如果你直接clone并cd进入项目目录，那么需要运行task_web.py文件
python src/celestialflow/task_web.py --port 5005 
```

默认监听端口 `5000`，但为了避免冲突，测试代码中使用的都是端口 `5005`，访问：

👉 [http://localhost:5005](http://localhost:5005)

可查看任务结构、执行状态、错误日志、以及实时注入任务等功能。

下图为运行测试时 web 页面的显示情况，非默认打开样式：

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>gif图压缩了过多细节(｡•́︿•̀｡)</em></p>

注意: 如果你没有启动Web窗口，同时设置了

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

那么[日志](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persistence/core_log.md)中会有一些`WARNING`，那是 TaskReporter 在提示无法连接 TaskWeb。但这并不影响使用。

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## 运行测试示例

项目提供了多个位于 `tests/` 目录下的示例文件，用于快速了解框架特性。

为了保证测试正常运行，建议直接在仓库根目录执行：

```bash
uv sync --group dev
```

之后推荐先运行以下测试：

```bash
pytest tests/test_graph.py
pytest tests/test_stage.py
```

- `tests/test_graph.py` 包含图结构相关测试：DAG 构建、分层调度、线程模式、循环/网格/完全图结构等。
- `tests/test_stage.py` 包含 Stage 节点相关测试：模式校验、标签生成、序列化检查等。

在代码运行过程中可以通过Web监视页面查看运行情况。
