# tests/ 测试总览

> 📅 最后更新日期: 2026/09/09

## 说明

本目录收集 `tests/` 下 pytest 测试集的中文说明文档，用于帮助读者快速定位不同模块的覆盖范围、运行方式与回归风险点。

与 `demo/` 不同，这里关注的是“功能是否正确”；与 `bench/` 不同，这里不讨论性能，而是关注行为约束、边界情况和协议一致性。

## 推荐阅读顺序

如果你是第一次查看测试集，建议按下面顺序阅读：

1. `conftest.md`：先看测试辅助工具与共享初始化说明
2. `runtime/`：理解基础类型、队列、异常和调度原语的覆盖范围
3. `graph/`：理解图结构、任务拓扑的核心测试
4. `observability/`：最后看 Reporter 与上报链路的集成测试

## 文档索引

### 顶层入口

| 文档 | 说明 |
|------|------|
| `conftest.md` | 全局 fixture、测试辅助工具与共享初始化说明 |

### 子目录说明

| 文档 | 说明 |
|------|------|
| `funnel/test_inlet.md` / `test_spout.md` | Inlet / Spout 管道相关测试 |
| `graph/test_graph.md` 等 | `TaskGraph`、拓扑分析与结构导出相关测试 |
| `observability/test_observer.md` / `test_reporter.md` | 观察者、Reporter、注入与上报相关测试 |
| `persistence/test_lifecycle.md` 等 | 生命周期 / 日志 / sqlite 工具等持久化相关测试 |
| `runtime/test_envelope.md` 等 | 队列、信封、异常、估算器、计数器等基础运行时测试 |
| `benchmark/test_benchmark.md` / `test_clone.md` | `benchmark_graph` / `benchmark_executor` 基准测试与 clone 工具测试 |

## 如何使用

可以从项目根目录按模块运行：

```bash
pytest tests -v
pytest tests/runtime -v
pytest tests/graph -v
pytest tests/observability -v
```

也可以按关键字筛选：

```bash
pytest tests -k "executor or graph or reporter" -v
```

## 如何阅读

建议按下面方式使用这些文档：

- 你想知道某个模块“测没测到”：先看对应子目录的 `test_*.md`
- 你想知道某个具体行为“怎么测的”：看对应的 `test_*.md` 即可（子目录不再提供 `__init__.md`）
- 你想定位协议变更的影响面：优先看 `graph/`、`runtime/`、`persistence/`、`observability/` 这几组文档

## 注意事项

1. 一些测试依赖临时文件、sqlite、事件队列或 HTTP 上报链路，运行环境抖动可能影响执行时间，但不应影响断言结果。
2. 当生产协议发生变化时，测试文档通常需要与 `src/`、`demo/` 一起同步更新。
3. 如果你只想快速验证当前改动，优先运行与改动目录最接近的测试子集，而不是总是跑全量测试。
4. 本目录的子目录（`runtime/`、`graph/`、`funnel/`、`observability/`、`persistence/`、`benchmark/`）**均无 `__init__.py`**，因此不存在对应的 `__init__.md`。
