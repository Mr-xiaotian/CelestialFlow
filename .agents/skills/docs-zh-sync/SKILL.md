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

1. 用 `list_directory` / `find_path` 扫描 `src/`、`bench/`、`tests/`、`demo/` 以及对应的 `docs/zh-CN/` 目录。
2. 按以下区域拆分任务（每个子代理 **上限 15-20 个文件**）：

| 区域 | 子代理 Prompt 文件 | 覆盖内容 |
|------|-------------------|---------|
| runtime + graph | `subagent-runtime-graph.md` | `src/celestialflow/runtime/`, `src/celestialflow/graph/` |
| funnel + stage + observability + persistence | `subagent-funnel-stage-obs-persist.md` | `src/celestialflow/funnel/`, `stage/`, `observability/`, `persistence/` |
| utils + web (py, routes, templates) | `subagent-utils-web.md` | `src/celestialflow/__init__.py`, `utils/`, `web/` (除 static) |
| web/static (ts + css) | `subagent-web-static.md` | `src/celestialflow/web/static/ts/`, `static/css/` |
| tests | `subagent-tests.md` | `tests/` 全部 |
| bench + demo | `subagent-bench-demo.md` | `bench/`, `demo/` 全部 |

> 如果 `src/` 文件量较大，可进一步拆分 runtime 与 graph、funnel 与 stage 等。

### 阶段 3: 委派子代理

对每个区域，按以下方式组装子代理 prompt：

1. **读取** `_subagent-base.md`（共享规则）→ 获取路径映射、审计清单、写作规范、输出格式
2. **读取** 对应区域的 `subagent-*.md` → 获取文件清单 + 区域特化陷阱 + 区域差异化写作规则
3. **拼接** 为一条完整消息，注入当前日期 `YYYY/MM/DD`，通过 `spawn_agent` 委派

> 委派消息中应包含 `_subagent-base.md` 的**完整内容**和 `subagent-*.md` 的**完整内容**，因为子代理无法直接读取 Skill 目录下的文件。

**推荐并行度**：
- 审计阶段：3-5 个代理并行
- 写入阶段：4 个代理并行
- 如果所有代理可同时处理审计+写入（每个代理独立负责一个区域），可一次性并行委派 5-6 个代理

### 阶段 4: 汇总与交付

所有子代理完成后，汇总输出：

- 本次扫描的区域
- 更新或新建的文档路径（按区域分组）
- 发现的代码-文档不一致问题汇总（按严重度）
- 仍待人工确认的歧义点

如果只完成了部分区域，要明确列出已完成范围和剩余范围。

汇总完成后，提醒用户检查 `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `docs/zh-CN/other/` 中引用的类名/函数名/路径是否因本次变更而过期。

### 降级策略

如果当前环境不支持 `subagent`，则按同样的区域边界顺序串行执行，但在思考和输出中保持分区。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `src/celestialflow/web/static/js/*.js`
- 第三方依赖锁文件、图片、二进制资源
- `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `other/` 目录（无直接代码对应）
