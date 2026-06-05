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

## 路径映射规则

目标文档路径由源文档路径直接替换语言根目录得到：

```
docs/zh-CN/README.md           →  docs/en/README.md           →  docs/ja/README.md
docs/zh-CN/src/__init__.md     →  docs/en/src/__init__.md     →  docs/ja/src/__init__.md
docs/zh-CN/src/runtime/foo.md  →  docs/en/src/runtime/foo.md  →  docs/ja/src/runtime/foo.md
docs/zh-CN/tests/bar.md        →  docs/en/tests/bar.md        →  docs/ja/tests/bar.md
docs/zh-CN/other/baz.md        →  docs/en/other/baz.md        →  docs/ja/other/baz.md
```

> 不限于上述子目录 —— `docs/zh-CN/` 下的任意 `.md` 文件，只要存在镜像路径，都纳入同步范围。

### 新增与删除

- **zh-CN 有、en/ja 无** → 在 en/ja 中新建对应文件，全文翻译。
- **zh-CN 无、en/ja 有** → 在 en/ja 中删除该文件（视为已废弃内容），并在最终汇总中列出已删除路径。
- **zh-CN 目录存在、en/ja 无** → 在 en/ja 中创建空目录结构，等待后续文件填充。

## 执行策略

### 区域划分

三个语言区域天然独立，优先并行处理：

| 区域 | 目标语言 | 说明 |
|------|:--------:|------|
| EN | English | `docs/en/` |
| JA | 日本語 | `docs/ja/` |

由于 en 和 ja 互不依赖，两个区域可以完全并行执行。每个区域内部如文件数量较大（>30 个），可按 `docs/zh-CN/` 的子目录进一步拆分：

- `docs/zh-CN/src/` 下各模块（`runtime/`、`graph/`、`stage/`、`funnel/`、`web/` 等）
- `docs/zh-CN/bench/`、`docs/zh-CN/tests/`、`docs/zh-CN/demo/`、`docs/zh-CN/other/`
- 根级文件（`README.md`、`quick_start.md`、`tutorial.md`、`change_log.md`、`presentation.md`）

每个 `subagent` 负责：

- 比对所属 zh-CN 文件与对应 en/ja 文件
- 判断"翻译 / 更新 / 删除 / 跳过"
- 忠实翻译，不添加或删减 zh-CN 中没有的信息
- 返回该区域的变更清单

### 执行流程

按以下步骤推进：

1. **前置检查**：确认 `docs/zh-CN/`、`docs/en/`、`docs/ja/` 三个目录均存在。若 en/ja 不存在则创建空目录。
2. **差异检测**：扫描 `docs/zh-CN/` 下所有 `.md` 文件，逐文件比对对应 en/ja 文档。判定依据：
   - zh-CN 的 `最后更新日期` 晚于 en/ja 的同字段 → **需更新**
   - zh-CN 文件存在但 en/ja 不存在 → **需新建**
   - zh-CN 文件不存在但 en/ja 存在 → **需删除**
   - 日期相同或 en/ja 更新 → **跳过**
3. **按区域翻译**：对每个需要处理的文件，读取 zh-CN 全文，逐段翻译到目标语言。
4. **写入**：将译文写入对应的 en/ja 路径。
5. **汇总**：输出完整的变更清单。

### 并行规则与效率

- **en 和 ja 天然并行**：两个语言区域无依赖，可同时释放 subagent。
- **推荐两阶段流水线**：差异检测 → 批量翻译。先扫完全部差异，再集中翻译写入。不要在同一个 agent 里边扫描边翻译，容易遗漏。
- **每个 agent 上限 15-20 个文件**：文件过多时 agent 难以维持翻译质量，超过此数量应进一步拆分区域。

### 降级策略

如果当前环境不支持真正的 `subagent`，则按 EN → JA 顺序串行执行，但在思考和输出中保持分区。

## 翻译规则

### 核心原则

- **zh-CN 是唯一事实来源**：翻译时不得添加 zh-CN 中没有的信息，也不得删减 zh-CN 中已有的信息。
- **忠实优先于优美**：优先保证技术含义准确，其次才是目标语言的自然流畅。
- **术语一致性**：同一技术术语在整份文档中的译法应保持一致。建议首次出现时在译文后附原文（如 "TaskGraph（任务图）"）。

### 内容分类处理

翻译时按内容类别区别对待：

| 内容类型 | 处理方式 |
|----------|---------|
| 中文正文段落 | **翻译**为目标语言 |
| 中文标题 (`#`, `##`, `###` 等) | **翻译**为目标语言 |
| 代码块 (` ```python `, ` ```bash ` 等) | **原样保留**（含代码注释） |
| Mermaid 图表 (` ```mermaid `) | **原样保留**节点 ID 和结构，仅翻译节点标签中的中文文本和 `subgraph` 标题 |
| HTML 标签（`<img>`, `<a>`, `<p>` 等） | **原样保留** |
| URL / 文件路径 | **原样保留** |
| 内联代码 (`` `code` ``) | **原样保留** |
| Markdown 表格 | **翻译**表头及单元格文字内容，保持列对齐 |
| 引用块 (`>`) | **翻译**引用内容 |
| 列表项 (`-`, `1.`) | **翻译**列表文字 |

### 日期本地化

更新日期行按语言本地化，日期值取 zh-CN 的同值：

| 语言 | 日期行格式 |
|------|-----------|
| zh-CN | `> 📅 最后更新日期: YYYY/MM/DD` |
| en | `> 📅 Last Updated: YYYY/MM/DD` |
| ja | `> 📅 最終更新日: YYYY/MM/DD` |

规则：

- 如果 zh-CN 文档**有**日期行 → 在译文对应位置写入本地化日期行，日期值取 zh-CN 的当日。
- 如果 zh-CN 文档**无**日期行 → 译文也不写日期行。
- 如果 en/ja 已有旧日期行但格式不对 → 修正为上述本地化格式，日期值同步为 zh-CN 的值。

### Mermaid 翻译细则

Mermaid 图表中仅翻译**面向读者的文本**，保留所有结构定义：

- ✅ 翻译：节点标签中的中文（如 `Graph[任务图]` → `Graph[Task Graph]`）、`subgraph` 标题中的中文
- ❌ 保留：节点 ID（如 `A`, `B`, `Graph`, `Queue`）、连线类型（`-->`, `--->`）、Mermaid 关键字（`flowchart`, `subgraph`, `end`）

示例：

```
原文：
flowchart LR
    A[开始] --> B{检查}
    B -->|是| C[执行]

en 译文：
flowchart LR
    A[Start] --> B{Check}
    B -->|Yes| C[Execute]
```

### 标题编号与锚点

zh-CN 中的标题可能不含编号，也可能含 `1.`、`1.1` 等编号。翻译时：

- 保留编号格式不变
- 仅翻译编号后的文字
- Markdown 锚点（`[text](#anchor)`）中的 `#anchor` 部分**原样保留**，仅翻译显示文本

## 文档质量要求

- 翻译结果应自然流畅，符合目标语言表达习惯。
- 技术术语优先使用业界通用译法。
- 长段落可适当拆分，避免译文出现"翻译腔"过重的超长句。
- 代码示例中的注释如果本身是中文，**不翻译**（注释面向开发者阅读源码时使用，翻译反而造成干扰）。
- 如果 zh-CN 中已经混有英文术语或英文句子，**原样保留**不翻译。

## 排除项

- `docs/zh-CN/` 本身（只读不写）。
- 非 `.md` 文件（图片、二进制资源等），即使存在于 `docs/` 目录下。
- 由其他 skill 负责的"代码 → zh-CN 文档"同步任务。

## 交付要求

完成后输出：

- 本次同步的语言区域（EN / JA / 两者）
- 更新的文档路径（按语言分组）
- 新建的文档路径（按语言分组）
- 删除的文档路径（按语言分组，如有）
- 发现的问题（如 zh-CN 中疑似错误、Mermaid 图表中未翻译的遗留文本等）

如果只完成了部分语言或部分区域，要明确列出已完成范围和剩余范围。
