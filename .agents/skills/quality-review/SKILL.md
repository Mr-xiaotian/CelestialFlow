---
name: "quality-review"
description: "Multi-agent code quality review across architecture, type safety, error handling, concurrency, refactoring, naming, and testability. Main agent processes areas serially, releasing parallel sub-agents per area."
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

主 agent 按区域**串行**推进（A → B → C → D → E → F），每个区域处理完毕再进入下一个。推荐拆成以下区域：

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

如果当前环境不支持真正的 `subagent`，则主 agent 自行按区域顺序逐一审查，每个区域内也按维度逐一检查（无法并行），但输出中仍需保持分区与维度标签。

### 执行效率建议

- **主 agent 串行，区域内并行**：主 agent 按 Group A → B → C → D → E → F 顺序逐一推进。每进入一个区域时，同时释放该区域的所有 subagent（如 Group A 同时释放 Architecture、Type Safety、Error & Edge、Refactoring、Naming & Style），等待全部返回并聚合后再进入下一区域。
- **推荐三阶段流水线**：审计 → 审查 → 汇总。先全面了解代码结构，再逐区域派发 agent，最后聚合报告。每次切换阶段前用 diagnostics 确认无新问题。
- **每个 subagent 上限 5-10 个文件**：文件过多时 subagent 难以维持对每个文件的细致关注，超过此数量应将区域进一步拆分。

## 推荐工作流

1. 读取项目 `src/` 目录，按模块划分审查区域（Group A~F）。每个区域应是一个**独立的文件夹**或**逻辑上紧密的文件夹组**。
2. **按区域顺序处理**：从 Group A 开始，逐区域推进。每进入一个区域时：
   - 读取该区域的所有代码文件，梳理关键类职责与模块交互关系
   - **并行释放该区域的所有 subagent**，每个 subagent 负责一个不同的检查方向：

     | agent | 检查方向 |
     |-------|---------|
     | **Architecture Agent** | 模块职责、层次依赖、设计模式、接口一致性 |
     | **Type Safety Agent** | 类型标注完整性、`Any` 逃逸、`type: ignore` 必要性、类型收窄 |
     | **Error & Edge Agent** | 异常处理覆盖、边界条件、资源泄漏风险、死代码 |
     | **Concurrency Agent** | 线程安全、锁使用、竞态条件、队列生命周期 |
     | **Refactoring Agent** | 重复代码、过长函数/类、圈复杂度、可提取的公共逻辑、过度嵌套、Magic Number |
     | **Naming & Style Agent** | 命名一致性、代码风格、注释质量、文档字符串完整性 |
     | **Testability Agent** | 可测试性、接口隔离、Mock 友好度、依赖注入缺口 |

   - 等待该区域所有 subagent 返回报告，汇总该区域结果
   - 然后进入下一个区域

3. 每个 subagent 的 prompt 必须包含：
   - 模块的**文件列表**
   - **关键类的职责**描述
   - **与周边模块的交互关系**（上游依赖、下游消费者）
   - 该 agent **重点关注的检查清单**（见下方各区域审查上下文）

4. 全部区域处理完毕后，去重、排序、生成最终报告。

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

## 执行策略

1. **主 agent 按区域串行推进**：从 Group A 到 Group F，逐个区域处理
2. **区域内 subagent 并行释放**：进入一个区域后，将该区域所有检查方向的 subagent 同时派发，互不依赖
3. **等待当区全部返回后聚合**：收集该区域所有 subagent 报告，汇总后再进入下一区域
4. **全部区域完成后输出最终报告**：Markdown 格式，顶部总览 + 各模块详情 + 评分

## 交付要求

完成后输出：

- 本次审查的区域
- 发现问题的总数与分布（按严重级别和模块）
- 仍待人工确认的歧义点
- 评分总览（如有）

如果只完成了部分区域，要明确列出已完成范围和剩余范围。
