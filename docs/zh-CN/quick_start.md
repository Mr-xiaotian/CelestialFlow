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

## （可选）配置状态上报

当前主仓已不再内置 Web 服务。如果示例代码中启用了 `TaskReporter`，你可以把它指向自建 HTTP 服务或独立的 `celestialflow-web` 项目；如果你只想体验 CelestialFlow 的核心调度能力，这一节可以直接跳过。

配置状态上报可以通过 `set_reporter` 来实现:

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

如果你启用了 `TaskReporter`，但目标服务没有启动，
[日志](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/src/persistence/core_log.md)
中会看到一些 `WARNING`。这表示 Reporter 无法连接远程服务，但并不影响任务图本身运行。

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
pytest tests/graph/test_graph.py
pytest tests/stage/test_stage.py
```

- `tests/graph/test_graph.py` 包含图结构相关测试：DAG 构建、分层调度、线程模式、循环/网格/完全图结构等。
- `tests/stage/test_stage.py` 包含 Stage 节点相关测试：模式校验、标签生成、序列化检查等。

在代码运行过程中，你可以通过日志、`TaskProgress` 进度条或状态快照查看运行情况。
