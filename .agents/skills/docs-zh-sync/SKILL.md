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

| # | 子任务 | 负责扫描的代码目录/文件 |
|---|--------|------------------------|
| 1 | src/runtime + graph | `src/celestialflow/runtime/*.py`<br>`src/celestialflow/graph/*.py` |
| 2 | src/funnel + stage + observability + persistence | `src/celestialflow/funnel/*.py`<br>`src/celestialflow/stage/*.py`<br>`src/celestialflow/observability/*.py`<br>`src/celestialflow/persistence/*.py` |
| 3 | src/包入口 + benchmark | `src/celestialflow/__init__.py`<br>`src/celestialflow/benchmark/*.py` |
| 4 | tests/runtime + graph | `tests/runtime/*.py`<br>`tests/graph/*.py` |
| 5 | tests/其余 | `tests/__init__.py`<br>`tests/conftest.py`<br>`tests/funnel/*.py`<br>`tests/stage/*.py`<br>`tests/observability/*.py`<br>`tests/persistence/*.py`<br>`tests/benchmark/*.py` |
| 6 | bench | `bench/*.py` |
| 7 | demo | `demo/*.py` |

执行步骤：

1. **调用全局扫描脚本** 生成对照清单（Manifest）。脚本与平台无关，跨 Windows / macOS / Linux：

   ```bash
   # 单行调用。$HOME 在 Bash 与 PowerShell 下均会自动展开为主目录（Windows 下为 %USERPROFILE%）。
   uv run python $HOME/.agents/skills/docs-zh-sync/scan_manifest.py --project-root . --pairs src/celestialflow/runtime:docs/zh-CN/src/runtime src/celestialflow/graph:docs/zh-CN/src/graph ...
   ```

   脚本输出 Markdown 三表格式（`exists` / `missing` / `orphans`）或 JSON，可直接复制进子代理 prompt。多 pair 场景直接在 `--pairs` 后空格分隔追加。

2. **核对 Manifest 分类**：
   - `exists`：代码与文档都存在 → 需审计内容一致性。
   - `missing`：代码存在但无对应文档 → 需新建。
   - `orphans`：文档存在但无对应源码 → 需删除或移动。

3. **利用脚本的重命名候选提示**。脚本在 `orphans` 表的"处理建议"列会标注"疑似重命名：X -> Y（相似度 0.56）"。重命名场景下（如源码 `util_serialize.py` 改名为 `util_render.py`），文档侧不需要新建，主 agent 应直接指引对应子代理把旧文档 `util_serialize.md` 改写为新文档 `util_render.md`，而不是让子代理临场判断。阈值可通过 `--rename-threshold` 调整（默认 0.5）。

### 委派子代理

按上述 7 个子任务，一次性并行委派 7 个子代理。每个子代理的消息中必须包含：

- 子任务编号和名称
- 当前日期 `YYYY/MM/DD`
- 该子任务的**代码→文档对照清单**（含孤立文档列表）
- **本区域本次需要重点核对的内容**（由主代理根据当前代码改动手写 2-3 条）
- 需要阅读的 Skill 文件路径：

| 顺序 | 文件 | 说明 |
|:----:|------|------|
| 1 | `~/.agents/skills/docs-zh-sync/_subagent-base.md` | 通用规则、输出格式 |
| 2 | `~/.agents/skills/docs-zh-sync/_subagent-audit.md` | 通用审计清单 |
| 3 | `~/.agents/skills/docs-zh-sync/_subagent-writing.md` | 通用写作规范 |
| 4 | 项目内 `.agents/skills/docs-zh-sync/_subagent-base.md` | 项目专属路径映射 |

> **退化策略**：如果当前环境限制子代理读取外部 Skill 目录，可临时将通用文件和项目文件合并写入项目内的临时文件（如 `temp/docs-zh-sync/instructions-{子任务}.md`），让子代理读取该临时文件，执行完毕后删除。

**推荐并行度**：
- 正常环境下分批委派，可一次性并行委派 5-6 个代理。若环境受限，可分批执行，但需在最终汇总中明确已完成和剩余子任务。

**跨子任务边界协调**：

如果扫描发现某个文档的源码路径不在当前子任务范围内（孤立文档属于另一个子任务的分区），按以下规则处理：

- 由**源码所在子任务**负责该文档的移动/删除/更新。
- 主 agent 在委派消息中标注"该文件由 XX 子任务处理"，避免重复操作。
- 汇总时主 agent 交叉确认所有跨边界文档无遗漏、无冲突。

> 典型场景：`docs/zh-CN/src/runtime/core_dispatch.md` 的源码在 `stage/`——由子任务 #2 负责处理。

**对照清单模板**：

委派消息中的代码→文档对照清单统一使用以下三表格式，子代理按此解析：

```markdown
### 有代码且有文档（审计内容一致性）
| # | 代码文件 | 文档文件 |
|---|---------|---------|
| 1 | `path/to/file.py` | `docs/zh-CN/path/to/file.md` |

### 有代码但无文档（需新建）
| # | 代码文件 | 目标文档 |
|---|---------|---------|
| 1 | `path/to/file.py` | `docs/zh-CN/path/to/file.md` |

### 孤立文档（需移动/删除）
| # | 当前文档 | 源码实际位置 | 处理建议 |
|---|---------|-------------|---------|
| 1 | `docs/zh-CN/old/path.md` | `src/new/path.py` | 移动到 `docs/zh-CN/new/path.md` |
```

### 汇总与交付

所有子代理完成后，汇总输出：

- 本次扫描的区域
- 更新、新建、删除或移动的文档路径（按区域分组）
- 发现的代码-文档不一致问题汇总（按严重度）
- 仍待人工确认的歧义点

如果只完成了部分区域，要明确列出已完成范围和剩余范围。

汇总完成后，由主 agent 直接处理 `docs/zh-CN/` 顶层文件（README.md、tutorial.md、quick_start.md、presentation.md、change_log.md 等）和 `docs/zh-CN/other/`：

1. **列出所有顶层文档**。可使用 `scan_manifest.py` 的 `--top-level` 选项（如 `uv run python $HOME/.agents/skills/docs-zh-sync/scan_manifest.py --top-level docs/zh-CN --top-level docs/zh-CN/other`），或直接 `Get-ChildItem docs/zh-CN/*.md docs/zh-CN/other/*.md`。
2. **本次变更中涉及的旧名集合**（重命名/删除的 API、异常、路径、文件名、测试名等）由主 agent 从子代理汇报中汇总得出。
3. **逐文件扫描并修复**：对每个顶层文档用 `grep`（或 `rg` / `Grep` 工具）搜索旧名，命中后直接修改为新名；无法确定改写的（如 `change_log.md` 的历史记录）保留不动。
4. **修改的文档同步刷新"最后更新日期"**。

将处理结果直接写入汇总报告：

```markdown
### 顶层文档处理

| 检查项 | 结果 |
|--------|:----:|
| 旧 API `start_graph()` / `start_db()` | ✅ 已替换为 `start()` / `start_db()`（行 12、45） |
| 旧路径 `tests/utils/` / `src/utils/` | ✅ 无残留 |
| 旧类名 `FallbackInlet` | 🔴 presentation.md L23、L67；已替换为 `LifecycleInlet` |
| ... | ... |

涉及文件：`quick_start.md`、`tutorial.md`、`presentation.md`。
```

### 降级策略

如果当前环境不支持 `subagent`，则按上述 7 个子任务顺序串行执行，每个子任务作为一个独立分区，输出格式仍遵循 `_subagent-base.md` 的要求。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `*.js`
- 第三方依赖锁文件、图片、二进制资源
