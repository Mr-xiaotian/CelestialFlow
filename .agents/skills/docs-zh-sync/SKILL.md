---
name: "docs-zh-sync"
description: "Audits code in src/, bench/, tests/, and demo/, then updates matching docs/zh-CN markdown by mirrored relative paths. Invoke when code changes require Chinese docs sync."
---

# Docs Zh Sync（CelestialFlow 项目配置）

本文件是 CelestialFlow 项目的 `docs-zh-sync` 技能专属配置，引用通用框架 `~/.agents/skills/docs-zh-sync/`。

当用户提出以下需求时，立即调用本技能：

- 同步、补全、刷新中文文档
- 依据代码更新 `docs/zh-CN`
- 检查 `src/`、`bench/`、`tests/`、`demo/` 后批量修正文档
- 发现文档过期、缺页、路径不一致，要求按代码现状修复

## 通用框架

本技能基于通用框架 `~/.agents/skills/docs-zh-sync/SKILL.md`，该框架定义了：

- 4 阶段执行流程（时间确认 → 扫描与区域划分 → 委派子代理 → 汇总与交付）
- 通用审计清单（`_subagent-audit.md`）
- 通用写作规范（`_subagent-writing.md`）
- 通用输出格式与降级策略

主 agent 在执行时，应优先遵循通用框架的流程，并结合本文件的以下项目特化配置。

---

## 项目特化：子任务划分

### 扫描与区域划分

按以下 **7 个固定子任务** 拆分。每个子任务文件量控制在 15–20 个以内，主 agent 不需要再做额外判断。

| # | 子任务 | 子代理 Prompt 文件 | 负责扫描的代码目录/文件 |
|---|--------|-------------------|------------------------|
| 1 | src/runtime + graph | `subagent-runtime-graph.md` | `src/celestialflow/runtime/*.py`<br>`src/celestialflow/graph/*.py` |
| 2 | src/funnel + stage + observability + persistence | `subagent-funnel-stage-obs-persist.md` | `src/celestialflow/funnel/*.py`<br>`src/celestialflow/stage/*.py`<br>`src/celestialflow/observability/*.py`<br>`src/celestialflow/persistence/*.py` |
| 3 | src/utils + package entry | `subagent-utils.md` | `src/celestialflow/__init__.py`<br>`src/celestialflow/utils/*.py` |
| 4 | tests/runtime + graph | `subagent-tests.md` | `tests/runtime/*.py`<br>`tests/graph/*.py` |
| 5 | tests/其余 | `subagent-tests.md` | `tests/__init__.py`<br>`tests/conftest.py`<br>`tests/funnel/*.py`<br>`tests/stage/*.py`<br>`tests/observability/*.py`<br>`tests/persistence/*.py`<br>`tests/utils/*.py` |
| 6 | bench | `subagent-bench-demo.md` | `bench/*.py` |
| 7 | demo | `subagent-bench-demo.md` | `demo/*.py` |

执行步骤：

1. 用 `find_path` 或 `terminal` 扫描每个子任务对应的代码目录，生成该子任务的代码文件清单。
2. 按项目路径映射规则（见 `_subagent-base.md`）推算每个代码文件对应的 `docs/zh-CN/` 目标文档路径。
3. 同时扫描对应 `docs/zh-CN/` 目录，找出"有文档但无对应源码"的孤立文件，单独列出。

### 委派子代理

按上述 7 个子任务，一次性并行委派 7 个子代理。每个子代理的消息中必须包含：

- 子任务编号和名称
- 当前日期 `YYYY/MM/DD`
- 该子任务的**代码→文档对照清单**（含孤立文档列表）
- 需要阅读的 Skill 文件路径：

| 顺序 | 文件 | 说明 |
|:----:|------|------|
| 1 | `~/.agents/skills/docs-zh-sync/_subagent-base.md` | 通用规则、输出格式 |
| 2 | `~/.agents/skills/docs-zh-sync/_subagent-audit.md` | 通用审计清单 |
| 3 | `~/.agents/skills/docs-zh-sync/_subagent-writing.md` | 通用写作规范 |
| 4 | 项目内 `.agents/skills/docs-zh-sync/_subagent-base.md` | 项目专属路径映射 |
| 5 | 项目内 `.agents/skills/docs-zh-sync/subagent-*.md` | 区域特化提示 |

> **退化策略**：如果当前环境限制子代理读取外部 Skill 目录，可临时将通用文件和项目文件合并写入项目内的临时文件（如 `temp/docs-zh-sync/instructions-{子任务}.md`），让子代理读取该临时文件，执行完毕后删除。

**推荐并行度**：
- 正常环境下分批委派，可一次性并行委派 5-6 个代理。若环境受限，可分批执行，但需在最终汇总中明确已完成和剩余子任务。

### 汇总与交付

所有子代理完成后，汇总输出：

- 本次扫描的区域
- 更新、新建、删除或移动的文档路径（按区域分组）
- 发现的代码-文档不一致问题汇总（按严重度）
- 仍待人工确认的歧义点

如果只完成了部分区域，要明确列出已完成范围和剩余范围。

汇总完成后，提醒用户检查 `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `docs/zh-CN/other/` 中引用的类名/函数名/路径是否因本次变更而过期。建议提供以下快速检查项：

- [ ] 搜索顶层文档中是否仍出现本次已重命名/删除的类名（如 `FailInlet` → `FallbackInlet`、`get_tag()` → `get_name()` 等）
- [ ] 搜索顶层文档中是否仍出现已变更的构造方式（如 `TaskGraph()` 无参构造、`BaseInlet(queue)` 旧式构造等）
- [ ] 搜索顶层文档中是否仍引用已删除的 API 端点、CSS 类名、测试文件名
- [ ] 检查 `docs/zh-CN/other/` 中是否有因代码重构而过时的算法说明或架构图

### 降级策略

如果当前环境不支持 `subagent`，则按上述 9 个子任务顺序串行执行，每个子任务作为一个独立分区，输出格式仍遵循 `_subagent-base.md` 的要求。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `*.js`
- 第三方依赖锁文件、图片、二进制资源
- `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `other/` 目录（无直接代码对应）
