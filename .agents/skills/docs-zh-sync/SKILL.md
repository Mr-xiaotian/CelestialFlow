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

1. 用 `find_path` 或 `terminal` 扫描每个子任务对应的代码目录，生成该子任务的代码文件清单。
2. 按项目路径映射规则（见 `_subagent-base.md`）推算每个代码文件对应的 `docs/zh-CN/` 目标文档路径。
3. 同时扫描对应 `docs/zh-CN/` 目录，找出"有文档但无对应源码"的孤立文件，单独列出。

**扫描提速**：步骤 1–3 可使用以下 Shell 模板一次生成镜像路径对照表（替换 `SRC_DIR` 和 `DOC_DIR` 为对应子任务的目录）：

```bash
# 生成代码→文档镜像路径对照表
# 用法: 替换 SRC_DIR 为代码目录, DOC_DIR 为 docs/zh-CN 对应目录
SRC_DIR="src/celestialflow/runtime"
DOC_DIR="docs/zh-CN/src/runtime"
for f in $(find "$SRC_DIR" -maxdepth 1 -name '*.py' ! -name '__pycache__' | sort); do
  base=$(basename "$f")
  doc="${base%.py}.md"
  doc="${doc/__init__.py/__init__.md}"
  if [ -f "$DOC_DIR/$doc" ]; then
    echo "📄 $f -> $DOC_DIR/$doc  (exists)"
  else
    echo "🆕 $f -> $DOC_DIR/$doc  (missing)"
  fi
done
# 找出孤立文档
for d in $(find "$DOC_DIR" -maxdepth 1 -name '*.md' | sort); do
  base=$(basename "$d")
  src="${base%.md}.py"
  src="${src/__init__.md/__init__.py}"
  if [ ! -f "$SRC_DIR/$src" ]; then
    echo "🗑 $d  (orphan, no source)"
  fi
done
```

> 提示：主 agent 可将该模板适配到每个子任务的目录后运行，用输出结果直接构建对照清单。

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

汇总完成后，由主 agent 自行扫描 `docs/zh-CN/` 顶层文件（README.md、tutorial.md、quick_start.md、presentation.md、change_log.md 等）和 `docs/zh-CN/other/`，检查引用的类名/函数名/路径是否因本次变更而过期。

扫描方式：使用 `grep` 搜索本次变更中涉及的旧名（重命名/删除的 API、异常、路径、文件名等），无需读取或修改文件内容。

将扫描结果直接汇报给用户，格式如下：

```markdown
### 顶层文档快速检查

| 检查项 | 结果 |
|--------|:----:|
| 旧 API `start_graph()` / `start_db()` | ✅/🔴 匹配行: ... |
| 旧路径 `tests/utils/` / `src/utils/` | ✅ 无残留 |
| ... | ... |

涉及文件：`quick_start.md`、`tutorial.md`、...
```

> 注意：此步骤**只扫描不修改**，仅向用户汇报发现。

### 降级策略

如果当前环境不支持 `subagent`，则按上述 7 个子任务顺序串行执行，每个子任务作为一个独立分区，输出格式仍遵循 `_subagent-base.md` 的要求。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/en/`
- `docs/ja/`
- 生成产物，如 `*.js`
- 第三方依赖锁文件、图片、二进制资源
- `docs/zh-CN/` 顶层文件（README.md、tutorial.md 等）和 `other/` 目录（无直接代码对应）
  > ⚠️ 此排除仅限制**修改/新建/删除**操作。汇总阶段的**扫描检查（只读）**不受此限制。
