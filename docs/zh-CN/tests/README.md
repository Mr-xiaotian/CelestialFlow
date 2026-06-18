# tests/ 测试总览

> 📅 最后更新日期: 2026/06/18

## 说明

本目录收集 `tests/` 下 pytest 测试集的中文说明文档，用于帮助读者快速定位不同模块的覆盖范围、运行方式与回归风险点。

与 `demo/` 不同，这里关注的是“功能是否正确”；与 `bench/` 不同，这里不讨论性能，而是关注行为约束、边界情况和协议一致性。

## 推荐阅读顺序

如果你是第一次查看测试集，建议按下面顺序阅读：

1. `tests/__init__.md`：先看测试目录总结构
2. `runtime/__init__.md`：理解基础类型、队列、异常和调度原语的覆盖范围
3. `stage/__init__.md` 与 `graph/__init__.md`：理解执行器、stage、任务图的核心测试
4. `web/__init__.md` 与 `observability/__init__.md`：最后看 Web 与上报链路的集成测试

## 文档索引

### 顶层入口

| 文档 | 说明 |
|------|------|
| `__init__.md` | `tests/` 目录结构与运行方式总说明 |
| `conftest.md` | 全局 fixture、测试辅助工具与共享初始化说明 |

### 子目录说明

| 文档 | 说明 |
|------|------|
| `funnel/__init__.md` | Inlet / Spout 管道相关测试 |
| `graph/__init__.md` | `TaskGraph`、拓扑分析与结构导出相关测试 |
| `observability/__init__.md` | 观察者、Reporter、注入与上报相关测试 |
| `persistence/__init__.md` | sqlite / JSONL / success / fail / log 持久化相关测试 |
| `runtime/__init__.md` | 队列、信封、异常、估算器、计数器等基础运行时测试 |
| `stage/__init__.md` | `TaskExecutor`、`TaskStage` 与内置 stage 相关测试 |
| `utils/__init__.md` | clone / format 等工具层测试 |
| `web/__init__.md` | Web 服务、路由与接口行为测试 |

## 如何使用

可以从项目根目录按模块运行：

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/stage -v
pytest tests/graph -v
pytest tests/web -v
```

也可以按关键字筛选：

```bash
pytest tests -k "executor or graph or reporter" -v
```

## 如何阅读

建议按下面方式使用这些文档：

- 你想知道某个模块“测没测到”：先看对应子目录的 `__init__.md`
- 你想知道某个具体行为“怎么测的”：再看对应的 `test_*.md`
- 你想定位协议变更的影响面：优先看 `graph/`、`stage/`、`persistence/`、`web/` 这几组文档

## 注意事项

1. 一些测试依赖临时文件、sqlite、事件队列或 Web 测试客户端，运行环境抖动可能影响执行时间，但不应影响断言结果。
2. 当生产协议发生变化时，测试文档通常需要与 `src/`、`web/`、`demo/` 一起同步更新。
3. 如果你只想快速验证当前改动，优先运行与改动目录最接近的测试子集，而不是总是跑全量测试。
