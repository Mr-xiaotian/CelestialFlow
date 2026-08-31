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

本项目当前**没有**项目根的 `README.md`，因此 `README.md` 不在本次同步范围内。如果未来出现根级 `README.md`，按 `scan_i18n_diff.py --root-file README.md` 的方式映射到 `docs/{en,ja}/README.md`。

---

## 日期行格式

子代理必须按主 agent 注入的 `{DATE_LABEL}` 写入日期行，**不要自行决定**格式：

- English: `> 📅 Last Updated: YYYY/MM/DD`
- 日本語: `> 📅 最終更新日: YYYY/MM/DD`

日期值取自 `docs/zh-CN/` 中对应文件的日期行。
