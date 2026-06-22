---
name: "docs-zh-sync"
description: "Audits code in src/, bench/, tests/, and demo/, then updates matching docs/zh-CN markdown by mirrored relative paths. Invoke when code changes require Chinese docs sync."
---

# Docs Zh Sync

用于把代码与 `docs/zh-CN` 文档持续对齐的技能。

当用户提出以下需求时，立即调用本技能：

- 同步、补全、刷新中文文档
- 依据代码更新 `docs/zh-CN`
- 检查 `src/`、`bench/`、`tests/`、`demo/` 后批量修正文档
- 发现文档过期、缺页、路径不一致，要求按代码现状修复

## 目标

检查 `src/`、`bench/`、`tests/`、`demo/` 中的 `*.py`、`*.ts`、`*.html`、`*.css` 文件，按镜像路径规则更新到 `docs/zh-CN/` 下的 `*.md` 文档。

## 执行流程（主 Agent 协调）

### 阶段 1: 时间确认

在开始任何文档更新前，**必须确认当前日期**。该日期将用于所有文档中的 `最后更新日期` 字段，格式为 `YYYY/MM/DD`。

- 优先从系统信息中的 `Today's Date` 字段获取。
- 若无法获取系统日期，应主动向用户确认。
- 同一批次的所有文档更新使用同一日期。
- **只更新本次实际修改过的文档的日期**；未修改的文档保持原有日期不变。

### 阶段 2: 扫描与区域划分

按以下 **9 个固定子任务** 拆分。每个子任务文件量控制在 15–20 个以内，主 agent 不需要再做额外判断。

| # | 子任务 | 子代理 Prompt 文件 | 负责扫描的代码目录/文件 |
|---|--------|-------------------|------------------------|
| 1 | src/runtime + graph | `subagent-runtime-graph.md` | `src/celestialflow/runtime/*.py`<br>`src/celestialflow/graph/*.py` |
| 2 | src/funnel + stage + observability + persistence | `subagent-funnel-stage-obs-persist.md` | `src/celestialflow/funnel/*.py`<br>`src/celestialflow/stage/*.py`<br>`src/celestialflow/observability/*.py`<br>`src/celestialflow/persistence/*.py` |
| 3 | src/utils + web（不含 static） | `subagent-utils-web.md` | `src/celestialflow/__init__.py`<br>`src/celestialflow/utils/*.py`<br>`src/celestialflow/web/*.py`（不含 `static/` 子目录） |
| 4 | src/web/static/css | `subagent-web-static.md` | `src/celestialflow/web/static/css/*.css` |
| 5 | src/web/static/ts | `subagent-web-static.md` | `src/celestialflow/web/static/ts/*.ts` |
| 6 | tests/runtime + graph | `subagent-tests.md` | `tests/runtime/*.py`<br>`tests/graph/*.py` |
| 7 | tests/其余 | `subagent-tests.md` | `tests/__init__.py`<br>`tests/conftest.py`<br>`tests/funnel/*.py`<br>`tests/stage/*.py`<br>`tests/observability/*.py`<br>`tests/persistence/*.py`<br>`tests/utils/*.py`<br>`tests/web/*.py` |
| 8 | bench | `subagent-bench-demo.md` | `bench/*.py` |
| 9 | demo | `subagent-bench-demo.md` | `demo/*.py` |

执行步骤：

1. 用 `Glob` 或 `Shell` 扫描每个子任务对应的代码目录，生成该子任务的代码文件清单。
2. 按镜像规则推算每个代码文件对应的 `docs/zh-CN/` 目标文档路径。
3. 同时扫描对应 `docs/zh-CN/` 目录，找出"有文档但无对应源码"的孤立文件，单独列出。

### 阶段 3: 委派子代理

按阶段 2 的 9 个子任务，一次性并行委派 9 个子代理。每个子代理的消息中必须包含：

- 子任务编号和名称
- 当前日期 `YYYY/MM/DD`
- 该子任务的**代码→文档对照清单**（含孤立文档列表）
- 需要阅读的 Skill 文件路径（子代理直接读取项目内的 `.agents/skills/docs-zh-sync/` 目录）：
  - `_subagent-base.md`（路径映射、源文件删除/移动处理、输出格式）
  - `_subagent-audit.md`（审计清单）
  - `_subagent-writing.md`（写作规范、表达形式、文档骨架）
  - 本子任务对应的 `subagent-*.md`

主 agent 不再需要在每次委派时完整注入 `_subagent-base.md` 等内容；只需在 prompt 中给出文件路径和待处理清单。

> **退化策略**：如果当前环境限制子代理读取 Skill 目录，可临时将 `_subagent-base.md`、`_subagent-audit.md`、`_subagent-writing.md` 与对应 `subagent-*.md` 的内容合并写入项目内的临时文件（如 `temp/docs-zh-sync/instructions-{子任务}.md`），让子代理读取该临时文件，执行完毕后删除。

**推荐并行度**：
- 正常环境下分批委派，可一次性并行委派 5-6 个代理。若环境受限，可分批执行，但需在最终汇总中明确已完成和剩余子任务。

### 阶段 4: 汇总与交付

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

如果当前环境不支持 `subagent`，则按阶段 2 的 9 个子任务顺序串行执行，每个子任务作为一个独立分区，输出格式仍遵循 `_subagent-base.md` 的要求。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `src/celestialflow/web/static/js/*.js`
- 第三方依赖锁文件、图片、二进制资源
- `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `other/` 目录（无直接代码对应）
