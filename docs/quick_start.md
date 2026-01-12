# 快速开始（Quick Start）

本节将引导你快速安装并运行 **TaskGraph**，通过示例体验其任务图调度机制。

## 创建独立虚拟环境

建议在独立环境中使用，以避免与其他项目依赖冲突。

```bash
# 使用 mamba 创建环境
mamba create -n celestialflow_env python=3.10
mamba activate celestialflow_env
```

可将mamba语句改为conda，如果你更习惯后者。如果你想尝试Mamba，你可以在这里获取它的最新版安装包 [miniforge/Releases](https://github.com/conda-forge/miniforge/releases)。

## 安装 CelestialFlow

CelestialFlow 已发布至 [PyPI](https://pypi.org/project/celestialflow/)，可以直接通过 `pip` 安装，无需克隆源码。

```bash
# 直接安装最新版
pip install celestialflow
```

不过如果你想要运行之后的测试代码，亦或者想使用基于Go语言的go_worker程序，那么还是需要clone项目

```bash
# 克隆项目
git clone https://github.com/Mr-xiaotian/CelestialFlow.git
cd CelestialFlow
pip install .
```

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
celestialflow-web 5005

# 如果你直接clone并cd进入项目目录，那么需要运行py文件
python src/celestialflow/task_web.py 5005 
```

默认监听端口 `5000`，但为了避免冲突，测试代码中使用的都是端口 `5005`，访问：

👉 [http://localhost:5005](http://localhost:5005)

可查看任务结构、执行状态、错误日志、以及实时注入任务等功能。

下图为运行test_graph_1时web页面的显示情况, 非默认打开样式：

![WebUI](https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/web_ui.gif)
<p align="center"><em>gif图压缩了过多细节(｡•́︿•̀｡)</em></p>

注意: 如果你没有启动Web窗口，同时设置了

```python
graph.set_reporter(True, host="127.0.0.1", port=5005)
```

那么[日志](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_logging.md)中会有一些`WARNING`，那是 TaskReporter 在提示无法连接 TaskWeb。但这并不影响使用。

```log
2025-12-10 08:57:13 WARNING [Reporter] Task injection fetch failed: ConnectTimeout
```

## 运行测试示例

项目提供了多个位于 `tests/` 目录下的示例文件，用于快速了解框架特性。

为了保证测试正常运行, 请先安装必要的测试库:
```bash
pip install pytest pytest-asyncio
```

之后推荐先运行以下两个示例：

```bash
pytest tests/test_graph.py::test_graph_1
pytest tests/test_nodes.py::test_splitter_1
```

- test_graph_1() 在一个简单的树状任务模型下，对比了四种运行组合（节点模式：serial / process × 执行模式：serial / thread），以测试不同调度策略下的整体性能差异。图结构如下:
    ```
    +----------------------------------------------------------------------+
    | Stage_A (stage_mode: serial, func: sleep_random_A)                   |
    | ╘-->Stage_B (stage_mode: serial, func: sleep_random_B)               |
    |     ╘-->Stage_D (stage_mode: serial, func: sleep_random_D)           |
    |         ╘-->Stage_F (stage_mode: serial, func: sleep_random_F)       |
    |     ╘-->Stage_E (stage_mode: serial, func: sleep_random_E)           |
    | ╘-->Stage_C (stage_mode: serial, func: sleep_random_C)               |
    |     ╘-->Stage_E (stage_mode: serial, func: sleep_random_E) [Visited] |
    +----------------------------------------------------------------------+
    ```
- test_splitter_0() 模拟了一个爬虫程序的执行流程：从入口页面开始抓取，并在解析过程中动态生成新的爬取任务并返回上游抓取节点；下游节点负责数据清洗与结果处理。图结构如下:
    ```
    +--------------------------------------------------------------------------------+
    | GenURLs (stage_mode: process, func: generate_urls_sleep)                       |
    | ╘-->Loger (stage_mode: process, func: log_urls_sleep)                          |
    | ╘-->Splitter (stage_mode: process, func: _split)                          |
    |     ╘-->Downloader (stage_mode: process, func: download_sleep)                 |
    |     ╘-->Parser (stage_mode: process, func: parse_sleep)                        |
    |         ╘-->GenURLs (stage_mode: process, func: generate_urls_sleep) [Visited] |
    +--------------------------------------------------------------------------------+
    ```

在代码运行过程中可以通过Web监视页面查看运行情况。