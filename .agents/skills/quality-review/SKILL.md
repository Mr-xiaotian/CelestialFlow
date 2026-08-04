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

使用多组 subagent 对项目进行全面的代码质量审查。每个审查区域分配一组 subagent，组内每个 agent 从不同维度独立检查同一片代码。最终汇总所有 agent 的报告，生成统一的质量评估。

## 执行流程（主 Agent 协调）

### 阶段 1: 扫描与区域划分

1. 用 `list_directory` 扫描 `src/` 目录结构。
2. 按模块划分审查区域。推荐分组：

| Group | 覆盖范围 | 审查维度 |
|-------|---------|---------|
| A | `graph/` | Architecture, Type Safety, Error & Edge, Refactoring, Naming & Style |
| B | `stage/` | Architecture, Type Safety, Error & Edge, Concurrency, Refactoring, Testability |
| C | `runtime/` | Architecture, Type Safety, Concurrency, Refactoring, Naming & Style |
| D | `observability/` + `persistence/` + `funnel/` | Architecture, Error & Edge, Refactoring |
| E | `utils/` | Architecture, Refactoring, Naming & Style |

> 实际分组应基于扫描结果动态调整。如果某区域文件量过大（>10 个），进一步拆分子区域。

### 阶段 2: 委派子代理（区域内并行，区域间串行）

主 agent **按 Group A → B → C → D → E 顺序串行推进**。每进入一个区域时：

1. **读取** 该区域所有代码文件，梳理关键类职责与模块交互关系
2. **读取** `_subagent-base.md`（共享规则）→ 获取报告格式、严重级别等
3. **读取** 该区域对应维度的 `subagent-*.md` → 获取各维度特化检查清单
4. **同时释放** 该区域所有维度的子代理，互不依赖
5. **等待全部返回**后聚合该区域结果，再进入下一区域

每个子代理的 prompt 必须包含：
- `_subagent-base.md` 的完整内容
- 对应 `subagent-*.md` 的完整内容
- 该区域的**代码文件列表**
- **关键类的职责**描述
- **与周边模块的交互关系**（上游依赖、下游消费者）

子代理维度与对应 Prompt 文件：

| agent | 检查方向 | Prompt 文件 |
|-------|---------|------------|
| **Architecture Agent** | 模块职责、层次依赖、设计模式、接口一致性 | `subagent-architecture.md` |
| **Type Safety Agent** | 类型标注完整性、`Any` 逃逸、`type: ignore` 必要性、类型收窄 | `subagent-type-safety.md` |
| **Error & Edge Agent** | 异常处理覆盖、边界条件、资源泄漏风险、死代码 | `subagent-error-edge.md` |
| **Concurrency Agent** | 线程安全、锁使用、竞态条件、队列生命周期 | `subagent-concurrency.md` |
| **Refactoring Agent** | 重复代码、过长函数/类、圈复杂度、可提取的公共逻辑 | `subagent-refactoring.md` |
| **Naming & Style Agent** | 命名一致性、代码风格、注释质量、文档字符串完整性 | `subagent-naming-style.md` |
| **Testability Agent** | 可测试性、接口隔离、Mock 友好度、依赖注入缺口 | `subagent-testability.md` |

### 阶段 3: 汇总与交付

全部区域处理完毕后，去重、排序、生成最终报告。

报告按以下格式组织：

```markdown
# Code Quality Review Report

## 📊 总览

| 区域 | 文件数 | 🔴 Critical | 🟡 Warning | 🟢 Info | 评分 |
|------|:------:|:-----------:|:----------:|:-------:|:----:|
| graph/ | N | N | N | N | ?/10 |
| stage/ | N | N | N | N | ?/10 |
| ... | | | | | |
| **合计** | **N** | **N** | **N** | **N** | **?.?/10** |

> 若无跨模块循环依赖，在此处下方注明 `✅ 未发现跨模块循环依赖`。

## 🌐 跨模块依赖问题

> 由主 agent 在汇总阶段对全部模块的 import 关系做拓扑检查后输出（见「跨模块依赖审计」）。
> 若无环，直接写 `✅ 未发现跨模块循环依赖`，不列出空项。

- **{环的完整路径，如 graph/ ↔ runtime/}** @ `{文件}:{行号}` — [架构/跨模块]
  - 影响: ...
  - 建议: ...

## 🔴 Critical Issues

> 按区域分组，仅列出所有子代理报告中的 🔴 项。

### graph/
- **{标题}** @ `{文件}:{行号}` — [{维度}]
  - 影响: ...
  - 建议: ...

### stage/
...

## 🟡 Warnings

> 仅列出需要关注的 🟡 项。

### graph/
...

## 🟢 Info

> 仅列出值得改进的 🟢 项。

### graph/
...

## 📋 各区域详细报告

> 将各子代理报告按区域聚合，去重后输出。

### graph/

#### Architecture
（子代理报告内容）

#### Type Safety
（子代理报告内容）

...

### stage/
...

## ⚠️ 仍待确认的歧义点
- ...
```

#### 去重规则

不同维度的 subagent 可能发现同一问题。去重时：
- 如果多个 agent 报告了**同一文件同一行**的问题 → 保留严重级别最高的，合并描述
- 如果问题类似但定位不同 → 各自保留

#### 跨模块依赖审计

单个子代理只审查自己区域的代码，跨模块的循环依赖必须由主 agent 在汇总阶段统一检查：

1. **汇总依赖表**：主 agent 基于已读取的代码与各子代理报告，提取每个模块的 import 关系，形成模块级依赖表：

   | 模块 | 导入的模块 |
   |------|-----------|
   | graph/ | runtime/, stage/ |
   | runtime/ | graph/（如 `util_estimators` 导入了 `util_graph`） |
   | ... | ... |

2. **检测环**：对依赖表做拓扑检查。存在 模块A → 模块B 且 模块B → 模块A（或更长环 A → B → C → A）即为跨模块循环依赖。

3. **上报规则**：
   - 每个环记为一条 🔴 Critical 问题，维度标注 `[架构/跨模块]`
   - 输出到报告的 `## 🌐 跨模块依赖问题` 章节（位于 `## 🔴 Critical Issues` 之前）
   - 每条描述必须包含：环的完整路径（如 `graph/ → runtime/ → graph/`）、具体 import 位置（`文件:行号`）、打破环的建议（如将公共类型/算法下沉到共享包、按单向依赖调整模块归属）

4. 若全部模块无环，在总览下方注明 `✅ 未发现跨模块循环依赖`，无需新建章节。

#### 评分规则

每个区域按以下公式计算评分（满分 10）：

```
评分 = round(10 × e^(-(0.12 × 🔴 + 0.04 × 🟡 + 0.01 × 🟢)), 1)
```

> 指数衰减保证评分始终落在 0~10 区间且保留区分度，避免线性减法在全面审查时大面积触底为 0。

常用参考值（用于自校验）：

| 🔴 | 🟡 | 🟢 | 评分 |
|:--:|:--:|:--:|:----:|
| 0 | 2 | 3 | 9.0 |
| 1 | 5 | 4 | 7.0 |
| 3 | 7 | 5 | 5.0 |
| 5 | 12 | 8 | 3.1 |
| 10 | 23 | 15 | 1.0 |

> 如果某区域文件较少（<3 个），评分参考价值有限，可标注"样本不足"。
> 若各区域评分普遍 >8.5 或 <1.5，说明子代理存在严重级别通胀/通缩，主 agent 应复核严重级别判定后再输出。

### 降级策略

如果当前环境不支持 `subagent`，则主 agent 自行按区域顺序逐一审查，每个区域内也按维度逐一检查（无法并行），但输出中仍需保持分区与维度标签。

## 排除项

- `tests/`、`bench/`、`demo/`（非核心业务代码）
- 第三方依赖、生成产物（`*.js`、`*.pyc`）
- 配置文件（`config.json`、`.env`）
