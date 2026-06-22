# Subagent Base Rules

> 本文件包含所有子代理共享的通用规则。
>
> 本 Skill 目录下另有：
> - `_subagent-audit.md`：审计清单
> - `_subagent-writing.md`：写作规范、表达形式、文档骨架
>
> 子代理应直接阅读上述文件，无需主 agent 在每次委派时完整注入。

---

## 必读文件清单

子代理开始工作前，请按顺序阅读：

1. `_subagent-base.md`（本文件）——路径映射、源文件删除/移动处理、输出格式
2. `_subagent-audit.md`——审计清单
3. `_subagent-writing.md`——写作规范、表达形式、文档骨架
4. 主 agent 指定的区域 `subagent-*.md`

---

## 路径映射规则

### 根目录映射

| 代码路径 | 文档路径 |
|---------|---------|
| `src/celestialflow/...` | `docs/zh-CN/src/...` |
| `bench/...` | `docs/zh-CN/bench/...` |
| `tests/...` | `docs/zh-CN/tests/...` |
| `demo/...` | `docs/zh-CN/demo/...` |

### 后缀映射

| 代码后缀 | 文档后缀 |
|:-------:|:-------:|
| `.py` | `.md` |
| `.ts` | `.md` |
| `.html` | `.md` |
| `.css` | `.md` |
| `__init__.py` | `__init__.md` |

### 示例

| 代码文件 | 文档文件 |
|---------|---------|
| `src/celestialflow/runtime/util_errors.py` | `docs/zh-CN/src/runtime/util_errors.md` |
| `src/celestialflow/web/static/ts/main.ts` | `docs/zh-CN/src/web/static/ts/main.md` |
| `src/celestialflow/web/templates/index.html` | `docs/zh-CN/src/web/templates/index.md` |
| `src/celestialflow/web/static/css/dashboard.css` | `docs/zh-CN/src/web/static/css/dashboard.md` |
| `tests/runtime/test_queue.py` | `docs/zh-CN/tests/runtime/test_queue.md` |
| `demo/demo_graph.py` | `docs/zh-CN/demo/demo_graph.md` |

如果项目里已经存在旧版但不镜像的中文文档路径，优先以"镜像路径"作为目标；必要时说明发现了旧路径遗留问题。

---

## 源文件删除/移动时的文档处理

审计时，除了检查文档内容是否正确，还要检查**文档本身是否还有对应的源文件**：

- 如果源码文件已被**删除**，则**删除对应的 `.md` 文档**。
- 如果源码文件已被**重命名/移动**，则**将对应的 `.md` 文档重命名/移动到新路径**，并更新内容。
- 在执行上述操作前，先确认新位置是否已有文档存在（可能是之前审计已创建）。

此规则也适用于 `__init__.py`：如果某个目录被移除或不再是一个 Python 包（无 `__init__.py`），对应的 `__init__.md` 也应删除。

---

## 输出格式（统一要求）

每个子代理完成后，**必须**按以下格式输出报告：

```markdown
## 区域: [名称]

### 更新文档 (N 个)
| 文件 | 严重度 | 修复内容 |
|------|:------:|---------|
| `docs/zh-CN/...` | 🔴/🟠/🟡 | 简要描述修复内容 |
| ... | | |

### 新建文档 (N 个)
| 文件 | 原因 |
|------|------|
| `docs/zh-CN/...` | 为什么需要新建 |
| ... | |

### 未修改文档 (N 个)
| 文件 | 原因 |
|------|------|
| `docs/zh-CN/...` | 审计通过，与源码一致 |
| ... | |

### 删除/移动文档 (N 个)
| 文件 | 操作 | 原因 |
|------|------|------|
| `docs/zh-CN/...` | 删除/重命名/移动 | 源码已删除/移动，或文档为孤立文档 |
| ... | | |

### 🔴 发现的主要不一致
| # | 文件 | 问题描述 |
|---|------|---------|
| 1 | ... | ... |

### ⚠️ 仍待确认的歧义点
- ...
```
