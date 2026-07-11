# Subagent Base Rules（CelestialFlow 项目专属）

> 本文件定义 CelestialFlow 项目的专属路径映射规则。
>
> 通用规则（输出格式、源文件删除/移动处理等）请参阅 `~/.agents/skills/docs-zh-sync/_subagent-base.md`。
>
> 开始工作前，请按顺序阅读：
> 1. `~/.agents/skills/docs-zh-sync/_subagent-base.md`（通用规则、输出格式）
> 2. `~/.agents/skills/docs-zh-sync/_subagent-audit.md`（通用审计清单）
> 3. `~/.agents/skills/docs-zh-sync/_subagent-writing.md`（通用写作规范）
> 4. 本文件（项目专属路径映射）
> 5. 主 agent 指定的区域 `subagent-*.md`

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
