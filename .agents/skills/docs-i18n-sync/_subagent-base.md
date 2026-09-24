# Subagent Base: I18n Translation Worker（CelestialFlow 项目特化）

> 本文件仅定义 CelestialFlow 项目的特化路径映射。**通用翻译规则（路径映射、操作规则、内容分类、Mermaid 细则、输出格式等）请参阅 `~/.agents/skills/docs-i18n-sync/_subagent-base.md`**。
>
> 开始工作前，请按顺序阅读：
> 1. `~/.agents/skills/docs-i18n-sync/_subagent-base.md`（通用翻译规则）
> 2. 本文件（项目特化路径映射）

---

## 项目路径映射

源语言为 `docs/zh-CN/`，目标语言为 `docs/{en,ja}/`，三者结构完全镜像。

### 镜像目录

| 源路径 (zh-CN) | 目标路径 (en/ja) |
|----------------|-----------------|
| `docs/zh-CN/src/...` | `docs/{en,ja}/src/...` |
| `docs/zh-CN/bench/...` | `docs/{en,ja}/bench/...` |
| `docs/zh-CN/tests/...` | `docs/{en,ja}/tests/...` |
| `docs/zh-CN/demo/...` | `docs/{en,ja}/demo/...` |
| `docs/zh-CN/other/...` | `docs/{en,ja}/other/...` |
| `docs/zh-CN/*.md`（顶层） | `docs/{en,ja}/*.md`（顶层） |

### 已知历史遗留

`docs/en/` 与 `docs/ja/` 历史上存在 `src/utils/` 与 `tests/utils/` 子目录，但 `docs/zh-CN/` 已无对应目录。脚本会将其识别为 `DELETE` 动作。

### 顶层特殊文件

本项目根存在 `README.md`（中文为主），**必须**翻译到 `docs/en/README.md` 与 `docs/ja/README.md`：
按 `scan_i18n_diff.py --root-file README.md` 的方式映射（源在项目根，不在 `docs/zh-CN/`）。
`docs/zh-CN/` 下**不放** `README.md` 镜像，故 `docs/{en,ja}/README.md` 不应被误判为 DELETE。

### H1 标题镜像（本项目强制）

`docs-zh-sync` 会把 `docs/zh-CN/` 的 H1 全量改为源码相对路径（如 `# src/celestialflow/node/core_node.py`），
且明确排除 en/ja。因此 en/ja 必须**逐字镜像**这类路径型 H1；总览类 README、`other/`、顶层文档的 H1 照常翻译。

### 代码块注释语言（本项目约定：本地化）

本项目 en/ja 既有语料约定：代码块中的**中文注释、docstring、示例输出文本一律本地化**（英/日），
仅保留标识符、结构、路径、URL。请与既有译文保持一致，**不要**在同一次同步中混用"保留中文"与"本地化"两种策略。

---

## 日期行格式

**日期值始终取自 `docs/zh-CN/` 中对应文件的日期行，与翻译时的"今天"无关**。这是"zh-CN 是唯一事实来源"原则的直接体现。

子代理必须按主 agent 注入的 `{DATE_LABEL}` 写入日期行，**不要自行决定格式或日期值**：

- English: `> 📅 Last Updated: YYYY/MM/DD`
- 日本語: `> 📅 最終更新日: YYYY/MM/DD`

日期值直接复制 `docs/zh-CN/` 对应文件的日期行。**禁止用"今天"或"当前日期"作为译文日期**。
