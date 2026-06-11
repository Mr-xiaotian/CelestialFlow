---
name: "docs-i18n-sync"
description: "Syncs translations from docs/zh-CN (source of truth) to docs/en/ and docs/ja/ by mirrored structure. Invoke when zh-CN docs have been updated and English/Japanese translations need to follow."
---

# Docs I18n Sync

用于以 `docs/zh-CN` 为唯一事实来源，将内容同步翻译至 `docs/en/`（英语）和 `docs/ja/`（日语）的技能。

当用户提出以下需求时，立即调用本技能：

- 同步、补全英文/日文文档
- 依据 `docs/zh-CN` 更新 `docs/en/` / `docs/ja/`
- 检查三语文档的一致性，修复翻译过期或缺失
- 发现 en/ja 文档与 zh-CN 内容、结构不一致，要求按 zh-CN 现状修复

## 目标

以 `docs/zh-CN/` 为唯一权威来源，将其全部内容忠实翻译到：

- `docs/en/` — 英语
- `docs/ja/` — 日语

两套译文的结构、文件名、目录树均与 `docs/zh-CN/` 完全镜像。

## 执行流程（主 Agent 协调）

### 阶段 1: 前置检查

1. 确认 `docs/zh-CN/` 存在且包含 `.md` 文件。
2. 若 `docs/en/` 或 `docs/ja/` 不存在，创建空目录结构（镜像 `docs/zh-CN/` 的目录树）。

### 阶段 2: 差异检测

扫描 `docs/zh-CN/` 下所有 `.md` 文件（递归），对每个文件判定与对应 en/ja 文档的状态：

| 条件 | 操作 |
|------|------|
| zh-CN 有，en/ja 无 | → **新建** |
| zh-CN 有，en/ja 有，但 zh-CN 的 `最后更新日期` 晚于 en/ja | → **更新** |
| zh-CN 有，en/ja 有，日期相同或 en/ja 更新 | → **跳过** |
| zh-CN 无，en/ja 有 | → **删除**（废弃内容） |

> 日期比较以文档开头的 `> 📅 最后更新日期:` / `> 📅 Last Updated:` / `> 📅 最終更新日:` 行中的 `YYYY/MM/DD` 值为准。

### 阶段 3: 委派子代理

en 和 ja **天然并行**，可同时委派两个子代理。

对每个目标语言，按以下方式组装 prompt：

1. **读取** `_subagent-base.md`（翻译规则）→ 获取路径映射、翻译规则、质量要求、输出格式
2. **注入** 目标语言参数：

| 参数 | EN | JA |
|------|:--:|:--:|
| 目标语言名 | English | 日本語 |
| 输出目录 | `docs/en/` | `docs/ja/` |
| 日期行格式 | `> 📅 Last Updated: YYYY/MM/DD` | `> 📅 最終更新日: YYYY/MM/DD` |

3. **注入** 差异检测结果（需要新建/更新/删除的文件清单，来自阶段 2）
4. 通过 `spawn_agent` 委派

> 委派消息中应包含 `_subagent-base.md` 的**完整内容**（子代理无法直接读取 Skill 目录下的文件）+ 本文件中的差异化参数 + 文件清单。

**并行度**：
- 如果待处理文件 ≤ 20 个：一个子代理处理整个语言
- 如果待处理文件 > 20 个：按 `docs/zh-CN/` 子目录拆分（`src/runtime/`、`src/graph/`、`bench/`、`tests/` 等），每个子代理上限 15-20 个文件

### 阶段 4: 汇总与交付

所有子代理完成后，汇总输出：

- 本次同步的语言区域（EN / JA / 两者）
- 更新的文档路径（按语言分组）
- 新建的文档路径（按语言分组）
- 删除的文档路径（按语言分组，如有）
- 发现的问题（如 zh-CN 中疑似错误、Mermaid 图表中未翻译的遗留文本等）

如果只完成了部分语言或部分区域，要明确列出已完成范围和剩余范围。

### 降级策略

如果当前环境不支持 `subagent`，则按 EN → JA 顺序串行执行，在思考和输出中保持分区。

## 排除项

- `docs/zh-CN/` 本身（只读不写）。
- 非 `.md` 文件（图片、二进制资源等）。
- 由其他 skill 负责的"代码 → zh-CN 文档"同步任务。
