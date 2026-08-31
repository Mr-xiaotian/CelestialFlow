---
name: "docs-i18n-sync"
description: "Syncs translations from docs/zh-CN (source of truth) to docs/en/ and docs/ja/ by mirrored structure. Invoke when zh-CN docs have been updated and English/Japanese translations need to follow."
---

# Docs I18n Sync（CelestialFlow 项目配置）

本文件是 CelestialFlow 项目的 `docs-i18n-sync` 技能专属配置，引用通用框架 `~/.agents/skills/docs-i18n-sync/`。

当用户提出以下需求时，立即调用本技能：

- 同步、补全英文/日文文档
- 依据 `docs/zh-CN` 更新 `docs/en/` / `docs/ja/`
- 检查三语文档的一致性，修复翻译过期或缺失
- 发现 en/ja 文档与 zh-CN 内容、结构不一致，要求按 zh-CN 现状修复

## 通用框架

本技能基于通用框架 `~/.agents/skills/docs-i18n-sync/SKILL.md`，该框架定义了：

- 4 阶段执行流程（时间确认 → 扫描与差异检测 → 委派子代理 → 汇总与交付）
- 通用翻译规则（`_subagent-base.md`）
- 通用输出格式与降级策略
- 跨平台扫描脚本 `scan_i18n_diff.py`（含重命名候选检测）

主 agent 在执行时，应优先遵循通用框架的流程，并结合本文件的以下项目特化配置。

---

## 项目特化：源 / 目标语言

| 角色 | 路径 | 日期行格式 |
|------|------|-----------|
| 源（唯一权威） | `docs/zh-CN/` | `> 📅 最后更新日期: YYYY/MM/DD` |
| 目标 1 | `docs/en/` | `> 📅 Last Updated: YYYY/MM/DD` |
| 目标 2 | `docs/ja/` | `> 📅 最終更新日: YYYY/MM/DD` |

## 项目特化：扫描命令

调用全局 `scan_i18n_diff.py` 生成翻译任务清单（Manifest）：

```bash
# 单行调用。$HOME 在 Bash 与 PowerShell 下均会自动展开为主目录（Windows 下为 %USERPROFILE%）。
uv run python $HOME/.agents/skills/docs-i18n-sync/scan_i18n_diff.py --project-root . --source docs/zh-CN --targets en:docs/en ja:docs/ja
```

> 注：脚本的 `--rename-threshold` 默认 0.5，可按需调整。

## 项目特化：子任务划分

EN 与 JA **天然并行**，可一次性并行委派 2 个子代理（每语言一个）。每个子代理的 FILES 清单中**不包含 SKIP 文件**（SKIP 由主 agent 自己从 Manifest 中过滤掉，传入子代理只会让 prompt 臃肿）。

| # | 子任务 | TARGET_LANG | OUTPUT_DIR | DATE_LABEL |
|---|--------|:-----------:|:----------:|:----------:|
| 1 | EN 翻译 | `English` | `docs/en/` | `> 📅 Last Updated:` |
| 2 | JA 翻译 | `日本語` | `docs/ja/` | `> 📅 最終更新日:` |

**分批策略**（参考全局框架，但 CelestialFlow 文件数较少时通常不触发）：

| 该语言待处理文件数 | 策略 |
|:-----------------:|------|
| ≤ 20 | 单代理处理整个语言 |
| 21–60 | 按 3 批拆分：① `bench/` + `demo/` + `other/` + 顶层文件 ② `src/`（全部子目录） ③ `tests/`（全部子目录） |
| > 60 | 在上述基础上，将 `src/` 和 `tests/` 按子目录进一步拆分，确保每批 ≤ 25 个文件 |

> 如果某批只有 SKIP 文件（无实际操作），可以省略该批。

## 委派子代理

每个子代理的消息中必须包含：

- 目标语言参数（见上表）
- 差异清单（来自 Manifest，仅保留该语言且非 SKIP 的动作）
- 需要阅读的 Skill 文件路径：

| 顺序 | 文件 | 说明 |
|:----:|------|------|
| 1 | `~/.agents/skills/docs-i18n-sync/_subagent-base.md` | 通用翻译规则、输出格式 |
| 2 | 项目内 `.agents/skills/docs-i18n-sync/_subagent-base.md` | 项目特化路径映射 |

> **退化策略**：如果当前环境限制子代理读取外部 Skill 目录，可临时将通用文件和项目文件合并写入项目内的临时文件（如 `temp/docs-i18n-sync/instructions-{lang}.md`），让子代理读取该临时文件，执行完毕后删除。

### Manifest 使用约定

主 agent 从脚本输出中读取每个语言区域的 5 类动作：

- `NEW` / `UPDATE` / `MOVE` / `DELETE` → 传给对应子代理处理
- `SKIP` → 主 agent 自己消费，不进入子代理 prompt

子代理无需理解"为什么是 SKIP"，只需要按 NEW/UPDATE/MOVE/DELETE 翻译即可。

## 顶层文件处理

CelestialFlow 当前在 `docs/zh-CN/` 顶层有以下文件：

- `change_log.md`、`presentation.md`、`quick_start.md`、`tutorial.md`

它们在 `docs/en/` 与 `docs/ja/` 中存在镜像，纳入常规扫描范围。脚本会自动识别并归入对应动作类别。

> **注意**：本项目目前**没有**项目根的 `README.md`（也不在 `docs/zh-CN/` 下）。如果未来引入根级 `README.md`，可通过 `scan_i18n_diff.py --root-file README.md` 纳入扫描范围。

## 排除项

除非用户明确要求，否则通常不处理：

- `docs/zh-CN/` 本身（只读不写）。
- 非 `.md` 文件（图片、二进制资源等）。
- 由 `docs-zh-sync` 技能负责的"代码 → zh-CN 文档"同步任务。
