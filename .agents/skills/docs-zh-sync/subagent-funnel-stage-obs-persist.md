# Subagent: Funnel + Stage + Observability + Persistence

> 覆盖 `src/celestialflow/funnel/`、`stage/`、`observability/`、`persistence/` 的中文文档。

## 文件清单

### funnel (3 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `src/celestialflow/funnel/__init__.py` | `docs/zh-CN/src/funnel/__init__.md` |
| 2 | `src/celestialflow/funnel/core_inlet.py` | `docs/zh-CN/src/funnel/core_inlet.md` |
| 3 | `src/celestialflow/funnel/core_spout.py` | `docs/zh-CN/src/funnel/core_spout.md` |

### stage (5 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `src/celestialflow/stage/__init__.py` | `docs/zh-CN/src/stage/__init__.md` |
| 2 | `src/celestialflow/stage/core_executor.py` | `docs/zh-CN/src/stage/core_executor.md` |
| 3 | `src/celestialflow/stage/core_stage.py` | `docs/zh-CN/src/stage/core_stage.md` |
| 4 | `src/celestialflow/stage/core_stages.py` | `docs/zh-CN/src/stage/core_stages.md` |
| 5 | `src/celestialflow/stage/util_types.py` | `docs/zh-CN/src/stage/util_types.md` |

### observability (4 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `src/celestialflow/observability/__init__.py` | `docs/zh-CN/src/observability/__init__.md` |
| 2 | `src/celestialflow/observability/core_observer.py` | `docs/zh-CN/src/observability/core_observer.md` |
| 3 | `src/celestialflow/observability/core_progress.py` | `docs/zh-CN/src/observability/core_progress.md` |
| 4 | `src/celestialflow/observability/core_report.py` | `docs/zh-CN/src/observability/core_report.md` |

### persistence (5 个)

| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `src/celestialflow/persistence/__init__.py` | `docs/zh-CN/src/persistence/__init__.md` |
| 2 | `src/celestialflow/persistence/core_fail.py` | `docs/zh-CN/src/persistence/core_fail.md` |
| 3 | `src/celestialflow/persistence/core_log.py` | `docs/zh-CN/src/persistence/core_log.md` |
| 4 | `src/celestialflow/persistence/core_success.py` | `docs/zh-CN/src/persistence/core_success.md` |
| 5 | `src/celestialflow/persistence/util_jsonl.py` | `docs/zh-CN/src/persistence/util_jsonl.md` |

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 虚构方法 | Inlet 类图中虚构 `put_item()`/`get_item()`，Executor 虚构 `process_result()`/`get_args()`/`unpack_task_args` | 逐方法对照源码 `def` 列表 |
| 🔴 异常类型错误 | 文档写 `NotImplementedError`，源码抛 `CelestialFlowError` | 追踪 `raise` 语句 |
| 🔴 虚构 API 推送端点 | Reporter 文档列 `/api/push_summary`，`_refresh_all()` 中不存在 | grep Reporter 源码中的 URL/路由注册 |
| 🟠 方法签名错误 | `start_graph` 参数签名与实际不符、`on_start` 传固定 `0` 而非实际 total | 逐方法对照 `__init__` 和公开方法签名 |
| 🟠 示例代码过时 | `LogInlet()` 无参调用、`stage.get_tag()` → `get_name()`、`await start_graph()` 应为同步 | 运行/审视文档中的每个示例 |
| 🟡 异常处理描述错误 | `_spout()` 文档写 `continue`，实际执行 `traceback.print_exc()` | 逐行阅读异常分支代码 |
| 🟡 内部实现描述错误 | JSONL 字段表虚构 `error`/`error_repr`/`task_repr` | 对照 dataclass 字段定义 |
| 🟢 文件归属错误 | `util_constant.py` 被错误归属于 `persistence/` | 确认文件实际路径 |

### 区域差异化写作规则

**funnel:**
- `core_inlet.py`：用 `classDiagram` 展示 Inlet 继承体系（`LogInlet`、`FailInlet`、`SuccessInlet`）。用 `sequenceDiagram` 展示 inlet → spout 的数据流。
- `core_spout.py`：用 `stateDiagram-v2` 展示 Spout 生命周期。重点说明 `_spout()` 循环中的异常处理和停止条件。

**stage:**
- `core_stage.py`：用 `stateDiagram-v2` 展示 TaskStage 状态转换。重点说明 `set_inlet`、`prev_bindings`、`drain_task_queue` 的协作。
- `core_executor.py`：用 `flowchart` 展示 Executor 生命周期（`on_start` → `_execute` → `on_end`）。说明同步/异步两种执行模式的区别。
- `core_stages.py`：重点说明 `TaskSplitter`、`TaskRouter`、`TaskMerger` 的流水线编排逻辑。

**observability:**
- `core_observer.py`：用 `classDiagram` 展示 Observer 体系。说明通知回调的注册和触发机制。
- `core_progress.py`：说明进度追踪的工作原理，示例中注意区分同步/异步调用。
- `core_report.py`：用表格列出所有推送方法及其对应的 Web API（**只列源码中实际存在的**）。用 `sequenceDiagram` 展示 `_refresh_all()` 的推送执行顺序。

**persistence:**
- `core_fail.py` / `core_success.py` / `core_log.py`：逐方法说明签名和用途。用 `flowchart` 展示持久化写入流程。
- `util_jsonl.py`：说明 JSONL 文件的读写格式和异常记录的解析逻辑。
- `__init__.md`：说明各持久化模块的分工和批量刷新策略。
