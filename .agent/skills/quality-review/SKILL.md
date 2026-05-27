---
name: "quality-review"
description: "Multi-agent code quality review across architecture, type safety, error handling, and concurrency. Invoke when code changes need comprehensive review."
---

# Code Quality Review Skill

用于对项目进行全面的代码质量审查的技能。

当用户提出以下需求时，立即调用本技能：

- 全面代码质量审查
- 按模块进行架构 / 类型安全 / 错误处理 / 并发安全审查
- 多维度自动审查代码并生成报告
- 检查 `src/` 下各模块的设计质量

## 目标

使用多组 subagent 对项目进行全面的代码质量审查。每个审查区域分配一个 **subagent 小组**，组内每个 agent 从不同维度独立检查同一片代码。最终汇总所有 agent 的报告，生成统一的质量评估。

## 分区执行策略

优先按区域拆分任务，并尽量使用 `subagent` 并行处理。推荐拆成以下区域：

| Group | 覆盖范围 | 成员 |
|-------|---------|------|
| A | `graph/` (TaskGraph, TaskChain, TaskCross 等) | Architecture, Type Safety, Error & Edge, Refactoring, Naming & Style |
| B | `stage/` (TaskExecutor, TaskStage, TaskSplitter, TaskRouter, TaskRedis*) | Architecture, Type Safety, Error & Edge, Concurrency, Refactoring, Testability |
| C | `runtime/` (queue, dispatch, envelope, metrics, types, errors, hash, estimators) | Architecture, Type Safety, Concurrency, Refactoring, Naming & Style |
| D | `observability/` + `persistence/` + `funnel/` | Architecture, Error & Edge, Refactoring |
| E | `web/` (TaskWebServer, FastAPI routes, templates, TS) | Architecture, Type Safety, Refactoring, Naming & Style |
| F | `utils/` (format, clone, benchmark, collections) | Architecture, Refactoring, Naming & Style |

如果代码量较大，可继续细分。

每个 `subagent` 负责：

- 扫描所属区域的代码文件
- 按指定的检查方向审查代码
- 返回结构化的审查报告
- 标注严重级别（🔴 Critical / 🟡 Warning / 🟢 Info）

如果当前环境不支持真正的 `subagent`，则按同样的区域边界顺序串行执行，但在思考和输出中保持分区。

### 执行效率建议

- **推荐三阶段流水线**：审计 → 审查 → 汇总。先全面了解代码结构，再批量派发 agent，最后聚合报告。每次切换阶段前用 `diagnostics` 确认无新问题。
- **并行规模**：所有 Group 的 subagent 可同时启动（无依赖），同组内的 agent 也可并行。
- **每个 agent 上限 15-20 个文件**：文件过多时 agent 难以维持对每个文件的细致关注，超过此数量应进一步拆分区域。

## 推荐工作流

1. 读取项目 `src/` 目录，按模块划分审查区域。每个区域应是一个**独立的文件夹**或**逻辑上紧密的文件夹组**。
2. 为每个区域派发 subagent 小组，组内包含 2~4 个 subagent，各自负责不同的检查方向：

   | agent | 检查方向 |
   |-------|---------|
   | **Architecture Agent** | 模块职责、层次依赖、设计模式、接口一致性 |
   | **Type Safety Agent** | 类型标注完整性、`Any` 逃逸、`type: ignore` 必要性、类型收窄 |
   | **Error & Edge Agent** | 异常处理覆盖、边界条件、资源泄漏风险、死代码 |
   | **Concurrency Agent** | 线程安全、锁使用、竞态条件、队列生命周期 |
   | **Refactoring Agent** | 重复代码、过长函数/类、圈复杂度、可提取的公共逻辑、过度嵌套、Magic Number |
   | **Naming & Style Agent** | 命名一致性、代码风格、注释质量、文档字符串完整性 |
   | **Testability Agent** | 可测试性、接口隔离、Mock 友好度、依赖注入缺口 |

3. 为每个 subagent 提供上下文，必须包含：
   - 模块的**文件列表**
   - **关键类的职责**描述
   - **与周边模块的交互关系**（上游依赖、下游消费者）
   - 该 agent **重点关注的检查清单**

4. 收集所有 subagent 报告，按模块汇总问题，标注严重级别，去重后生成最终报告。

## 报告的格式要求

每个 subagent 返回的报告应遵循统一格式：

```
## [{Group Name}] {Agent Name} Report

### Critical (🔴)
- {问题描述} @ {文件:行号}
  - 影响: ...
  - 建议: ...

### Warning (🟡)
- {问题描述} @ {文件:行号}
  - 影响: ...
  - 建议: ...

### Info (🟢)
- {观察} @ {文件:行号}
```

## 各区域审查上下文

以下是为 `CelestialFlow` 项目定制的区域划分与审查要点。其他项目请类比调整。

### Group A — `graph/` (TaskGraph, TaskChain, TaskCross 等)

**上下文**:

- 核心类: `TaskGraph`, `StageRuntime`(dataclass)
- 预置图结构: `TaskChain`, `TaskCross`, `TaskGrid`, `TaskLoop`, `TaskWheel`, `TaskComplete`
- 工具: `util_analysis.py`(networkx 图分析), `util_serialize.py`(结构序列化)
- 上游依赖: `stage/`, `runtime/`, `observability/`, `persistence/`
- 下游: Web 可视化通过 `get_*` 查询接口消费

**Architecture**:
- 图构建 → 执行的生命周期是否清晰
- `_build_resources` / `_build_analysis` / `_execute_stages` 的顺序是否合理
- 预置结构类是否在正确的位置（继承 vs 组合）
- 查询接口(`get_*`)是否泄漏内部状态

**Type Safety**:
- `stage_dict: dict[str, TaskStage]` 及相关类型是否一致
- 是否有可消除的 `type: ignore` 或 `Any`
- `StageRuntime` 的字段使用是否完整

**Error & Edge**:
- DAG/非 DAG 分支处理是否正确
- `_finalize_nodes` 中 drain 未消费任务的逻辑是否完整
- `put_stage_queue` 对不存在的 stage 只 `continue` 不报错是否合适
- 警告(RuntimeWarning)的使用是否恰当

**Refactoring**:
- `TaskChain`/`TaskCross` 等预置图类是否有可提取的共同逻辑（构建模式、验证逻辑）
- 图构建代码中是否有过长的 `_build_*` 方法可拆解
- `util_analysis.py` 和 `util_serialize.py` 的循环/递归逻辑是否有简化空间
- 可视化的 `get_*` 查询方法是否有重复的数据组装逻辑

**Naming & Style**:
- 图结构类的命名是否一致（`TaskGraph` vs `StageRuntime` 风格差异）
- 内部方法命名（`_build_*`, `_execute_*`, `_finalize_*`）是否遵循统一前缀约定
- 关键方法的 docstring 是否完整

---

### Group B — `stage/` (TaskExecutor, TaskStage, TaskSplitter, TaskRouter, TaskRedis*)

**上下文**:

- 核心类: `TaskExecutor`(基类), `TaskStage`(图节点), `TaskSplitter`, `TaskRouter`
- Redis 扩展: `TaskRedisTransport`, `TaskRedisSource`, `TaskRedisAck`
- 执行模式: serial / thread / async
- 上游依赖: `runtime/`, `persistence/`
- 下游: `graph/` 调度 stage, `TaskStage.start_stage()` 是图执行入口

**Architecture**:
- `TaskExecutor` → `TaskStage` → 子类的继承层次是否合理
- `init_env` / `_init_*` 拆分是否清晰
- `start()` vs `start_async()` vs `start_stage()` 的职责边界
- `put_task` / `put_signal` / `_put_task_queue` 的 public/private 划分

**Type Safety**:
- 类级注解 vs 实例属性的类型一致性
- `execution_mode` / `stage_mode` 字符串枚举是否应改为 `Literal` 或 `Enum`
- Redis 相关 `Any` 使用是否可收窄
- `dispatch` / spout / inlet 的 `reportUninitializedInstanceVariable` 是否可消除

**Error & Edge**:
- `process_task_success` / `handle_task_fail` 的异常路径
- Retry 逻辑: `emit_retry_envelope` 的 id 管理
- Redis 连接惰性初始化的线程安全
- `_source` / `_ack` 的超时与错误处理

**Concurrency**:
- `dispatch_thread` 中 ThreadPoolExecutor 生命周期
- `dispatch_async` 中 Semaphore + asyncio.Task 管理
- `ValueWrapper` / `SumCounter` 的锁使用
- `_init_spout` 线程启动时机与数据竞争

**Refactoring**:
- `start()` / `start_async()` / `start_stage()` 是否有大段重复的初始化/清理代码
- `TaskSplitter` 和 `TaskRouter` 的路由/分发逻辑是否可提取为公共策略
- `init_env` 中 `_init_*` 方法的调用是否有条件分支可简化
- 是否有可以提取为工具函数的重复模式（如 envelope 构建、queue 操作）

**Testability**:
- `TaskExecutor` 是否可直接实例化测试，还是必须依赖完整的图上下文
- `_source` / `_ack` (Redis) 是否有接口抽象以支持 Mock
- `dispatch` 方法是否强耦合 `ThreadPoolExecutor`，能否注入

---

### Group C — `runtime/` (queue, dispatch, envelope, metrics, types, errors, hash, estimators)

**上下文**:

- 核心: `TaskInQueue`(termination 合并), `TaskOutQueue`(广播), `TaskDispatch`(三种执行模式)
- 信封: `TaskEnvelope`(带 hash/ID/溯源)
- 指标: `TaskMetrics`(计数器, 去重), `ValueWrapper`, `SumCounter`
- 工具: `util_hash`, `util_types`, `util_errors`, `util_estimators`
- 上游: 被 `stage/` 和 `graph/` 消费
- 下游: 不依赖其他业务模块

**Architecture**:
- Queue 的 termination 合并协议是否正确处理所有上游组合
- `TaskDispatch._worker` / `_async_worker` 的重复代码是否可提取
- `TaskMetrics` 是否承担了过多职责(计数+去重+重试异常)
- `util_estimators.calc_global_remain_equal_pred` 的算法假设是否合理并有文档

**Type Safety**:
- `queue: Any` 是否可泛型化
- `CTreeEvent` 字符串常量是否应改为 `StrEnum`
- `TerminationSignal` / `TerminationIdPool` 的区分是否清晰

**Concurrency**:
- `dispatch_thread` 的 future 清理策略
- `dispatch_async` 的 `asyncio.to_thread` + Semaphore 组合
- `TaskMetrics` 在多线程下的原子性
- `drain()` 方法的 `get_nowait` + break 模式

**Refactoring**:
- `TaskDispatch._worker` / `_async_worker` 的重复代码是否可提取公共核心逻辑
- `TaskInQueue` / `TaskOutQueue` 是否有共享的 termination 处理模式可提取
- `util_estimators` 中的统计算法是否有重复的窗口/均值计算
- 各处 `envelope` 构建/校验代码是否有可以统一的工厂或 builder

**Naming & Style**:
- `util_errors.py` 中的异常类命名是否一致（`Error` vs `Exception` 后缀）
- `TaskMetrics` 的方法命名是否明确表达操作语义（`inc_*`/`add_*`/`record_*` 统一）
- 工具模块的公开函数是否有完整 docstring

---

### Group D — `observability/` + `persistence/` + `funnel/`

**上下文**:

- observability: `TaskProgress`(tqdm), `TaskReporter`(HTTP), `BaseObserver`
- persistence: `LogInlet/Spout`, `FailInlet/Spout`, `SuccessSpout`, `util_jsonl`
- funnel: `BaseInlet`(put 到队列), `BaseSpout`(后台线程消费)
- 上游: 被 `stage/`, `graph/` 通过 inlet/spout 模式解耦
- 下游: 写入文件(JSONL)、推送 HTTP、显示 tqdm 进度条

**Architecture**:
- Inlet/Spout 模式是否真正解耦了生产者和消费者
- `LogInlet` 方法数量(~30个)是否应拆分或参数化
- `TaskReporter` 的 pull/push 协议与 Web 端的耦合
- `NullTaskReporter` / `NullCelestialTreeClient` 空对象模式使用

**Error & Edge**:
- `BaseSpout._spout` 的 `except Exception: pass` 是否应至少记录日志
- `FailSpout` 的 JSONL 写入是否原子(并发写入)
- `LogSpout` 的批量 flush 策略是否合理
- `load_jsonl_logs` 跳过脏行的容错策略

**Refactoring**:
- `LogInlet` / `FailInlet` / `SuccessSpout` 的 JSONL 写入逻辑是否可提取公共基类方法
- `BaseSpout._spout` 的循环/休眠模式是否可抽象为通用的后台消费者
- `TaskProgress` / `TaskReporter` / `BaseObserver` 是否有共同的进度上报接口可提取
- 各 Spout 子类的 `_spout` 是否有重复的 try/except/cleanup 模板

---

### Group E — `web/` (TaskWebServer, FastAPI routes, templates, TS)

**上下文**:

- 核心: `TaskWebServer`(FastAPI), 路由定义在 `_setup_routes`
- 拉取: `pull_*` 系列 API(从 reporter 拉状态/错误)
- 推送: `push_*` 系列 API(reporter 推送到此)
- 前端: `templates/`, `static/ts/`, `static/js/`
- 工具: `util_config.py`, `util_error.py`, `util_cal.py`

**Architecture**:
- Pull/Push API 的对称性是否一致
- `_setup_routes` 是否应拆分为独立的 router 文件
- `WebConfigModel` / `DashboardConfigModel` 的配置管理
- 错误存储(`error_store`)的生命周期

**Type Safety**:
- FastAPI/pydantic 模型是否完整
- `reportMissingImports` / `reportUnknownMemberType` 是否可消除
- TypeScript 前端是否有类型问题

**Refactoring**:
- `pull_*` / `push_*` API handler 是否有重复的响应组装/错误处理逻辑
- `_setup_routes` 中的路由注册是否有重复的 pattern 可提取为装饰器或工厂
- TypeScript 前端模块是否有可提取的公共组件/工具函数
- `util_config.py` / `util_error.py` / `util_cal.py` 是否有边界模糊、职责重叠

**Naming & Style**:
- API 端点命名是否一致（`pull_*` vs `push_*` vs `get_*` 前缀规范）
- pydantic model 命名是否统一（`*Model` vs `*Config` suffix）
- TypeScript 变量/函数命名是否与 Python 端保持可对照

---

### Group F — `utils/` (format, clone, benchmark, collections)

**上下文**:

- `util_format`: 表格格式化, `format_repr`, `format_table`
- `util_clone`: executor/stage/graph 深拷贝
- `util_benchmark`: 性能基准测试
- `util_collections`: 字典按值聚类

**Architecture**:
- `clone_*` 系列是否完整覆盖所有需要克隆的属性
- `benchmark_*` 的测试是否覆盖全部执行模式组合
- `format_table` 的复杂度是否可简化

**Refactoring**:
- `util_clone` 中各 `clone_*` 函数是否有重复的属性复制逻辑可泛型化
- `util_format` 的格式化函数是否有共同的列宽计算/对齐逻辑可提取
- `util_benchmark` 的计时/统计代码是否可提取为装饰器或上下文管理器
- `util_collections` 的聚类算法是否有可优化的嵌套循环

**Naming & Style**:
- 工具函数命名是否遵循统一风格（`util_*` vs 公开函数名）
- Magic Number 是否可提取为模块级常量
- 每个公开函数是否有 docstring 说明参数和返回值

## 执行策略

1. **并行派发**: 所有 Group 的 subagent 可同时启动（无依赖）
2. **同组内也可并行**: 同一 Group 内的所有 agent（Architecture / Type Safety / Error & Edge / Concurrency / Refactoring / Naming & Style / Testability）互不依赖
3. **等待全部返回后聚合**: 收集所有报告，按严重级别和模块排序，去重
4. **输出最终报告**: Markdown 格式，顶部总览 + 各模块详情 + 评分

## 交付要求

完成后输出：

- 本次审查的区域
- 发现问题的总数与分布（按严重级别和模块）
- 仍待人工确认的歧义点
- 评分总览（如有）

如果只完成了部分区域，要明确列出已完成范围和剩余范围。
