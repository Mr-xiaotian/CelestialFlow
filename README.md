# CelestialFlow ——一个轻量级、可并行、基于图结构的 Python 任务调度框架

<p align="center">
  <img src="https://raw.githubusercontent.com/Mr-xiaotian/CelestialFlow/main/img/logo.png" width="1080" alt="CelestialFlow Logo">
</p>

<p align="center">
  <a href="https://pypi.org/project/celestialflow/"><img src="https://badge.fury.io/py/celestialflow.svg"></a>
  <a href="https://pepy.tech/projects/celestialflow"><img src="https://static.pepy.tech/personalized-badge/celestialflow?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/l/celestialflow.svg"></a>
  <a href="https://pypi.org/project/celestialflow/"><img src="https://img.shields.io/pypi/pyversions/celestialflow.svg"></a>
</p>

**CelestialFlow** 是一个轻量级但功能完全体的任务流框架，适合需要“灵活拓扑 + 多执行模式 + 可视化监控”的中/大型 Python 任务系统。

- 相比 Airflow/Dagster 更轻、更快开始
- 相比 multiprocessing/threading 更结构化，可直接表达 loop / complete graph 等复杂依赖

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

在此基础上项目支持 Web 可视化与通过 Redis 外接go代码，弥补 Python 在cpu密集任务上速度过慢的问题。

## 项目结构（Project Structure）

```mermaid
flowchart LR

    %% ===== TaskGraph =====
    subgraph TG[TaskGraph]
        direction LR

        S1[TaskStage A]
        S2[TaskStage B]
        S3[TaskStage C]
        S4[TaskStage D]

        T1[Last Stage]
        T2[Next Stage]

        TS[[TaskSplitter]]
        TR[/TaskRedisTransfer/]

        RE[(Redis)]
        G1((GoWorker))

        S1 --> S2 --> S3 --> S1
        S1 --> S4

        T1 -->|1 task| TS
        TS -->|N task| T2

        TR -->RE --> G1
        G1 -->RE --> TR

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 美化 TaskStages
    style S1 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style S2 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style S3 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style S4 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    
    style T1 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style T2 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px

    %% 美化 特殊Stage
    style TS fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style TR fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px

    %% 美化 外部结构
    style RE fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px
    style G1 fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px

    %% ===== WebUI =====
    subgraph W[WebUI]
        JS
        HTML
    end

    style W fill:#ffeaf0,stroke:#d66b8c,stroke-width:2px,rx:10px,ry:10px
    style JS fill:#ffffff,stroke:#d66b8c,rx:5px,ry:5px
    style HTML fill:#ffffff,stroke:#d66b8c,rx:5px,ry:5px

    R[TaskWeb]
    style R fill:#f0e9ff,stroke:#8a6bc9,stroke-width:2px,rx:8px,ry:8px

    %% ===== Links =====
    TG --> R 
    R --> TG 
    R --> W
    W --> R

```

## 快速开始（Quick Start）

安装 CelestialFlow:

```bash
pip install celestialflow
```

一个简单的可运行代码:

```python
from celestialflow import TaskManager, TaskGraph

def add(x, y): 
    return x + y

def square(x): 
    return x ** 2

if __name__ == "__main__":
    # 定义两个任务节点
    stage1 = TaskManager(add, execution_mode="thread", unpack_task_args=True)
    stage2 = TaskManager(square, execution_mode="thread")

    # 构建任务图结构
    stage1.set_graph_context([stage2], stage_mode="process", stage_name="Adder")
    stage2.set_graph_context([], stage_mode="process", stage_name="Squarer")
    graph = TaskGraph([stage1])

    # 初始化任务并启动
    graph.start_graph({stage1.get_stage_tag(): [(1, 2), (3, 4), (5, 6)]})
```

注意不要在.ipynb中运行。

👉 想查看完整Quick Start，请见[Quick Start](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/quick_start.md)

## 深入阅读（Further Reading）

(以下文档完善中)

你可以继续运行更多的测试代码，这里记录了各个测试文件与其中的测试函数说明：

[📄tests/README.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/tests/README.md)

若你想了解框架的整体结构与核心组件，下面的参考文档会对你有帮助：

- [🔧TaskManage/TaskStage概念](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_manage.md)
- [🌐TaskGrapg概念](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_graph.md)
- [📚Go Worker概念](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/go_worker.md)

推荐阅读顺序:

```mermaid
flowchart TD
    classDef whiteNode fill:#ffffff,stroke:#000000,color:#000000;

    TM[TaskManage] --> TG[TaskGraph]
    TM --> TP[TaskProgress]

    TG --> TQ[TaskQueue]
    TG --> TN[TaskNodes]
    TG --> TR[TaskReport]
    TG --> TS[TaskStructure]

    TR --> TW[TaskWeb]
    TN --> GW[Go Worker]

    class TM,TG,TP,TQ,TN,TR,TS,TW,GW whiteNode;
```

以下三篇可以作为补充阅读:

- [TaskTools](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_tools.md)
- [TaskTypes](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_types.md)
- [TaskLogging](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/task_logging.md)

如果你更喜欢通过完整案例理解框架的运行方式，可以参考这篇从零开始构建 TaskGraph 的教程：

[📘案例教程](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/tutorial.md)

## 环境要求（Requirements）

**CelestialFlow** 基于 Python 3.8+，并依赖以下核心组件。  
请确保你的环境能够正常安装这些依赖（`pip install celestialflow` 会自动安装）。

| 依赖包           | 说明 |
| ---------------- | ---- |
| **Python ≥ 3.8** | 运行环境，建议使用 3.10 及以上版本 |
| **tqdm**         | 控制台进度条显示，用于任务执行可视化 |
| **loguru**       | 高性能日志系统，支持多进程安全输出 |
| **fastapi**      | Web 服务接口框架（用于任务可视化与远程控制） |
| **uvicorn**      | FastAPI 的高性能 ASGI 服务器 |
| **requests**     | HTTP 客户端库，用于任务状态上报与远程调用 |
| **networkx**     | 任务图（TaskGraph）结构与依赖分析 |
| **redis**        | 可选组件，用于分布式任务通信（`TaskRedisTransfer` 模块） |
| **jinja2**       | FastAPI 模板引擎，用于 Web 可视化界面渲染 |

## 文件结构（File Structure）

```
📁 CelestialFlow	(205MB 169KB 76B)
    📁 experiments  	(14KB 536B)
        🐍 benchmark_datastructures.py	(5KB 796B)
        🐍 benchmark_hash.py          	(1KB 284B)
        🐍 benchmark_queue.py         	(5KB 185B)
        🐍 benchmark_tqdm.py          	(1KB 160B)
        🐍 experiment_tqdm.py         	(1KB 135B)
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
    📁 img          	(966KB 63B)
        📷 logo.png       	(836KB 542B)
        📷 web_display.png	(129KB 545B)
    📁 src          	(1MB 884KB 224B)
        📁 celestialflow         	(1MB 869KB 480B)
            📁 static     	(1MB 419KB 510B)
                📁 css	(32KB 568B)
                    🎨 base.css     	(6KB 155B)
                    🎨 dashboard.css	(8KB 435B)
                    🎨 errors.css   	(5KB 168B)
                    🎨 inject.css   	(12KB 834B)
                📁 js 	(34KB 868B)
                    📜 main.js          	(4KB 973B)
                    📜 task_errors.js   	(4KB 544B)
                    📜 task_injection.js	(8KB 491B)
                    📜 task_statuses.js 	(8KB 63B)
                    📜 task_structure.js	(7KB 143B)
                    📜 task_topology.js 	(261B)
                    📜 utils.js         	(1KB 441B)
                ❓ favicon.ico	(1MB 352KB 98B)
            📁 templates  	(12KB 973B)
                🌐 index.html	(12KB 973B)
            📁 [1项排除的目录]	(314KB 710B)
            📝 README.md        	(13KB 131B)
            🐍 task_graph.py    	(22KB 530B)
            🐍 task_logging.py  	(6KB 291B)
            🐍 task_manage.py   	(32KB 66B)
            🐍 task_nodes.py    	(4KB 953B)
            🐍 task_progress.py 	(1KB 477B)
            🐍 task_queue.py    	(7KB 896B)
            🐍 task_report.py   	(5KB 511B)
            🐍 task_structure.py	(6KB 93B)
            🐍 task_tools.py    	(15KB 182B)
            🐍 task_types.py    	(1KB 461B)
            🐍 task_web.py      	(5KB 47B)
            🐍 __init__.py      	(817B)
        📁 celestialflow.egg-info	(14KB 768B)
            ❓ PKG-INFO            	(13KB 363B)
            📄 [5项排除的文件]	(1KB 405B)
    📁 tests        	(113KB 510B)
        📁 [1项排除的目录]	(81KB 604B)
        📝 README.md        	(7KB 231B)
        🐍 test_graph.py    	(5KB 83B)
        🐍 test_manage.py   	(1KB 785B)
        🐍 test_nodes.py    	(7KB 864B)
        🐍 test_structure.py	(9KB 1015B)
    📁 [6项排除的目录]	(195MB 276KB 932B)
    ❓ .gitignore    	(264B)
    ❓ LICENSE       	(1KB 65B)
    ❓ Makefile      	(501B)
    ❓ pyproject.toml	(1KB 223B)
    ⚙️ pytest.ini    	(254B)
    📝 README.md     	(15KB 536B)
```

(该视图由我的另一个项目[CelestialVault](https://github.com/Mr-xiaotian/CelestialVault)中inst_file生成。)

## 更新日志（Change Log）

- [2021] 建立一个支持多线程与单线程处理函数的类
- [2023] 在GPT4帮助下添加多进程与携程运行模式 
- [5/9/2024] 将原有的处理类抽象为节点, 添加TaskChain类, 可以线性连接多个节点, 并设定节点在Chain中的运行模式, 支持serial和process两种, 后者Chain所有节点同时运行
- [12/12/2024-12/16/2024] 在原有链式结构基础上允许节点有复数下级节点, 实现Tree结构; 将原有TaskChain改名为TaskTree
- [3/16/2025] 支持Web端任务完成情况可视化
- [6/9/2025] 支持节点拥有复数上级节点, 脱离纯Tree结构, 为之后循环图做准备
- [6/11/2025] 自[CelestialVault](https://github.com/Mr-xiaotian/CelestialVault)项目instances.inst_task迁入
- [6/12/2025] 支持循环图, 下级节点可指向上级节点
- [6/13/2025] 支持loop结构, 即节点可指向自己
- [6/14/2025] 支持forest结构, 即可有多个根节点
- [6/16/2025] 多轮评测后, 当前框架已支持完整有向图结构, 故将TaskTree改名为TaskGraph

## Star 历史趋势（Star History）

如果对项目感兴趣的话，还请star。

[![Star History Chart](https://api.star-history.com/svg?repos=Mr-xiaotian/CelestialFlow&type=Date)](https://star-history.com/#Mr-xiaotian/CelestialFlow&Date)

## 许可（License）
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 作者（Author）
Author: Mr-xiaotian 
Email: mingxiaomingtian@gmail.com  
Project Link: [https://github.com/Mr-xiaotian/CelestialFlow](https://github.com/Mr-xiaotian/CelestialFlow)