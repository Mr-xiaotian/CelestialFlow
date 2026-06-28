# demo/ 演示总览

> 📅 最后更新日期: 2026/06/28

## 说明

本目录收集 `demo/` 下各类演示脚本的中文说明文档，帮助你快速了解 CelestialFlow 的核心能力、图结构表达方式、执行模式、观察者、Redis 集成与常用工具函数。

这些 demo 更偏向“上手体验”和“能力展示”，与 `bench/` 的性能对比、`tests/` 的行为校验定位不同。

## 推荐阅读顺序

如果你是第一次接触项目，建议按下面顺序阅读：

1. `demo_executor.md`：先理解 `TaskExecutor` 的基本执行方式
2. `demo_graph.md`：再看 `TaskGraph` 如何连接 stage 形成 DAG
3. `demo_structure.md`：继续看链、网格、环、完全图等结构化封装
4. `demo_observer.md`：最后看运行过程中的观察与进度展示

## 演示模块总览

| 文档 | 源码 | 演示目标 | 是否需要外部服务 |
|------|------|---------|:---------------:|
| `demo_executor.md` | `demo/demo_executor.py` | `TaskExecutor` 的 serial / thread / async 三种执行模式 | 否 |
| `demo_observer.md` | `demo/demo_observer.py` | 为 `TaskExecutor` 注册 `TaskProgress` 与自定义 `LoggingObserver` | 否 |
| `demo_funnel.md` | `demo/demo_funnel.py` | 脱离任务图，单独使用 `BaseInlet` / `BaseSpout` 构建事件采集管道 | 否 |
| `demo_graph.md` | `demo/demo_graph.py` | `TaskGraph` 的扇出/扇入 ETL 与异步分阶段流水线 | Reporter / CelestialTree（可选） |
| `demo_stages.md` | `demo/demo_stages.py` | `TaskSplitter`、`TaskRouter` 与链式/环状图结构 | Reporter / CelestialTree（可选） |
| `demo_structure.md` | `demo/demo_structure.py` | `TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete` 等预定义拓扑 | Reporter / CelestialTree（可选） |
| `demo_redis.md` | `demo/demo_redis.py` | 用普通 `TaskStage` 实现 Redis 任务投递、结果确认与外部任务源 | Redis、Reporter（可选） |
| `demo_utils.md` | `demo/demo_utils.py` | 各演示脚本共享的辅助函数与任务函数 | 否 |

> **注意**：表格中“是否需要外部服务”指直接运行默认入口时的强依赖；可选服务未就绪时通常只会跳过上报，不会导致 demo 退出。

## 文档索引

### 执行与任务图

| 文档 | 说明 |
|------|------|
| `demo_executor.md` | `TaskExecutor` 的串行 / 线程 / 异步执行演示 |
| `demo_graph.md` | DAG 任务图、ETL 流程与 staged/eager 调度演示 |
| `demo_structure.md` | `TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop` 等结构化图封装演示 |
| `demo_stages.md` | `TaskStage`、`TaskSplitter`、`TaskRouter` 等 stage 级能力说明 |

### 观察、管道与扩展

| 文档 | 说明 |
|------|------|
| `demo_observer.md` | 观察者、进度上报与生命周期回调演示 |
| `demo_funnel.md` | Inlet / Spout 管道行为与数据流转演示 |
| `demo_redis.md` | Redis 相关集成示例 |

### 辅助函数

| 文档 | 说明 |
|------|------|
| `demo_utils.md` | demo 中共用的辅助函数、输入构造与任务函数说明 |

## 如何使用

大多数 demo 都可以直接从项目根目录运行，例如：

```bash
python demo/demo_executor.py
python demo/demo_graph.py
python demo/demo_structure.py
```

某些 demo 会依赖额外环境，例如：

- Reporter 服务
- Redis 服务
- CelestialTree 服务

运行前请先查看对应单页文档中的“依赖”和“运行方式”章节。

## 注意事项

1. demo 的目标是展示能力，不一定追求最小依赖和最短运行时间。
2. 某些示例会连接外部服务，若环境变量或服务端未就绪，运行时会直接失败。
3. 如果你想看框架行为是否正确，请优先参考 `tests/`；如果你想看性能取舍，请优先参考 `bench/`。
