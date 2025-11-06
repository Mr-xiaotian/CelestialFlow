# CelestialFlow ——一个轻量级、可并行、基于图结构的 Python 任务调度框架

---

![](img/startup.png)

**CelestialFlow**是一个基于节点拼接的任务流调度框架。

框架的基本单元为 **TaskStage**（由 `TaskManager` 派生），每个 stage 内部绑定一个独立的执行函数，并支持四种运行模式：

* **线性（serial）**
* **多线程（thread）**
* **多进程（process）**
* **协程（async）**

每个 stage 均可独立运行，也可作为节点互相连接，形成具有上游与下游依赖关系的任务图（**TaskGraph**）。下游 stage 会自动接收上游执行完成的结果作为输入，从而实现数据的流动与传递。

在图级别上，TaskGraph 支持两种布局模式：

* **线性执行（serial layout）**：前一节点执行完毕后再启动下一节点（下游节点可提前接收任务但不会立即执行）。
* **并行执行（process layout）**：所有节点同时启动运行，由队列自动协调任务传递与依赖顺序。

TaskGraph 能构建完整的 **有向图结构（Directed Graph）**，不仅支持传统的有向无环图（DAG），也能灵活表达 **环形（loop）** 与 **复杂交叉** 的任务依赖。

这种设计使得开发者可以以最小的代码代价，快速搭建高并发、可扩展且可视化的任务调度系统。

---

## 快速开始（Quick Start）

本节将引导你快速安装并运行 **TaskGraph**，通过示例体验其任务图调度机制。


### 克隆项目并创建虚拟环境

首先从 GitHub 拉取代码仓库，并创建隔离环境以防依赖冲突。

```bash
# 克隆项目
git clone https://github.com/yourname/TaskGraph.git
cd TaskGraph

# (可选) 用mamba创建虚拟环境
mamba create -n celestialflow_env python=3.10
mamba activate celestialflow_env
```

如果你了解python的包管理工具Anaconda，那么mamba就是将其用C++实现的版本，非常好用。你可以在这里获取它的最新版:

👉 [miniforge/Releases](https://github.com/conda-forge/miniforge/releases)

### 安装依赖与环境初始化

```bash
pip install .
```

或开发模式安装（如果你打算修改代码并实时看到结果）：

```bash
pip install -e .
```

### 启动 Web 可视化（可选）

Web监视界面并不是必须的，但页面设计还不错，推荐使用:

```bash
python src/celestialflow/task_web.py 5005 
```

默认监听端口 `5000`，但为了避免冲突，测试代码中使用的都是端口 `5005`，访问：

👉 [http://localhost:5005](http://localhost:5005)

可查看任务结构、执行状态、错误日志、以及实时注入任务等功能。

![](img/web_display.png)

### 运行测试示例

项目提供了多个位于 `tests/` 目录下的示例文件，用于快速了解框架特性。
推荐先运行以下两个示例：

```bash
pytest tests/test_graph.py::test_graph_1
pytest tests/test_nodes.py::test_splitter_1
```

- test_graph_1() 在一个更简单的树状任务模型下，对比了四种运行组合（节点模式：serial / process × 执行模式：serial / thread），以测试不同调度策略下的整体性能差异。图结构如下:
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
- test_splitter_1() 模拟了一个爬虫程序的执行流程：从入口页面开始抓取，并在解析过程中动态生成新的爬取任务；下游节点负责数据清洗与结果处理。图结构如下:
    ```
    +--------------------------------------------------------------------------------+
    | GenURLs (stage_mode: process, func: generate_urls_sleep)                       |
    | ╘-->Loger (stage_mode: process, func: log_urls_sleep)                          |
    | ╘-->Splitter (stage_mode: process, func: _split_task)                          |
    |     ╘-->Downloader (stage_mode: process, func: download_sleep)                 |
    |     ╘-->Parser (stage_mode: process, func: parse_sleep)                        |
    |         ╘-->GenURLs (stage_mode: process, func: generate_urls_sleep) [Visited] |
    +--------------------------------------------------------------------------------+
    ```

在代码运行过程中可以通过Web监视页面查看运行情况。

### 我还想了解更多

你可以继续运行更多的测试代码，这里有介绍每个测试文件与里面的测试函数:
[Test RREADME.md](tests/README.md)

你也可以了解具体的项目文件，以下文档会帮助你:

[Src README.md](src\celestialflow/README.md)

如果你想得到一个最简单的可运行代码:

```python
from celestialflow import TaskManager, TaskGraph

def add(x, y): 
    return x + y

def square(x): 
    return x ** 2

# 定义两个任务节点
stage1 = TaskManager(add, execution_mode="thread")
stage2 = TaskManager(square, execution_mode="thread")

# 构建任务图结构
stage1.set_graph_context([stage2], stage_mode="process", stage_name="Adder")
graph = TaskGraph([stage1])

# 初始化任务并启动
graph.start_graph({stage1.get_stage_tag(): [(1, 2), (3, 4), (5, 6)]})
```

---

## 环境要求（Requirements）

**CelestialFlow** 依赖以下主要组件，请确保你的环境满足最低版本要求。

| 依赖包              | 说明                                  |
| ---------------- | ----------------------------------- |
| **Python ≥ 3.8** | 运行环境                                |
| **fastapi**      | Web 服务接口框架                          |
| **uvicorn**      | FastAPI 的高性能 ASGI 服务器               |
| **redis**        | 可选组件，用于分布式任务通信（TaskRedisTransfer） |
| **pytest**       | 单元测试框架                              |
| **multiprocess** | 多进程支持库                              |
| **rich**         | 终端输出与日志美化                           |
| **jinja2**       | FastAPI 模板引擎                        |

---

## 项目结构（Project Structure）

以下视图由我的另一个项目[CelestialVault](https://github.com/Mr-xiaotian/CelestialVault)中inst_file生成。

```
📁 CelestialFlow	(24MB 349KB 185B)
    📁 experiment   	(9KB 455B)
        🐍 experiment_queue.py	(4KB 1B)
        🐍 experiment_redis.py	(5KB 454B)
    📁 go_worker    	(6MB 967KB 64B)
        📁 worker	(5KB 684B)
            🌀 parser.go   	(394B)
            🌀 processor.go	(2KB 612B)
            🌀 types.go    	(237B)
            🌀 worker.go   	(2KB 465B)
        ❓ go.mod       	(258B)
        ❓ go.sum       	(591B)
        ❓ go_worker.exe	(6MB 960KB)
        🌀 main.go      	(579B)
    📁 img          	(129KB 545B)
        📷 startup.png	    (836KB)
        📷 web_display.png	(129KB 545B)
    📁 src          	(1MB 855KB 679B)
        📁 celestialflow         	(1MB 854KB 576B)
            📁 static     	(1MB 418KB 529B)
                📁 css	(32KB 164B)
                    🎨 base.css     	(6KB 114B)
                    🎨 dashboard.css	(8KB 463B)
                    🎨 errors.css   	(5KB 168B)
                    🎨 inject.css   	(12KB 443B)
                📁 js 	(34KB 267B)
                    📜 main.js          	(4KB 973B)
                    📜 task_errors.js   	(4KB 544B)
                    📜 task_injection.js	(8KB 437B)
                    📜 task_statuses.js 	(8KB 63B)
                    📜 task_structure.js	(6KB 620B)
                    📜 task_topology.js 	(261B)
                    📜 utils.js         	(1KB 441B)
                ❓ favicon.ico	(1MB 352KB 98B)
            📁 templates  	(12KB 924B)
                🌐 index.html	(12KB 924B)
            📝 README.md        	(11KB 385B)
            🐍 task_graph.py    	(25KB 477B)
            🐍 task_logging.py  	(5KB 369B)
            🐍 task_manage.py   	(36KB 81B)
            🐍 task_nodes.py    	(4KB 964B)
            🐍 task_progress.py 	(1KB 477B)
            🐍 task_report.py   	(5KB 996B)
            🐍 task_structure.py	(5KB 776B)
            🐍 task_tools.py    	(12KB 72B)
            🐍 task_types.py    	(1KB 338B)
            🐍 task_web.py      	(4KB 1015B)
            🐍 __init__.py      	(910B)
    📁 tests        	(97KB 158B)
        🐍 test_graph.py    	(5KB 763B)
        🐍 test_manage.py   	(1KB 721B)
        🐍 test_nodes.py    	(9KB 173B)
        🐍 test_structure.py	(10KB 827B)
    ❓ .gitignore	(271B)
    ❓ Makefile  	(501B)
    ⚙️ pytest.ini	(254B)
    📝 README.md 	(1KB 124B)
    🐍 setup.py  	(550B)
```

---

## 更新日志（Change Log）

- [2021] 建立一个支持多线程与单线程处理函数的类
- [2023] 在GPT4帮助下添加多进程与携程运行模式 
- [5/9/2024] 将原有的处理类抽象为节点, 添加TaskChain类, 可以线性连接多个节点, 并设定节点在Chain中的运行模式, 支持serial和process两种, 后者Chain所有节点同时运行
- [12/12/2024-12/16/2024] 在原有链式结构基础上允许节点有复数下级节点, 实现Tree结构; 将原有TaskChain改名为TaskTree
- [3/16/2025] 支持web端任务完成情况可视化
- [6/9/2025] 支持节点拥有复数上级节点, 脱离纯Tree结构, 为之后循环图做准备
- [6/11/2025] 自[CelestialVault](https://github.com/Mr-xiaotian/CelestialVault)项目instances.inst_task迁入
- [6/12/2025] 支持循环图, 下级节点可指向上级节点
- [6/13/2025] 支持loop结构, 即节点可指向自己
- [6/14/2025] 支持forest结构, 即可有多个根节点
- [6/16/2025] 多轮评测后, 当前框架已支持完整有向图结构, 故将TaskTree改名为TaskGraph

---

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 作者
Author: Xiaotian 
Email: mingxiaomingtian@gmail.com  
Project Link: [https://github.com/Mr-xiaotian/CelestialFlow](https://github.com/Mr-xiaotian/CelestialFlow)