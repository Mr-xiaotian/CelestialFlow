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
| `src/celestialflow/node/util_types.py` | `docs/zh-CN/src/node/util_types.md` |
| `src/celestialflow/__init__.py` | `docs/zh-CN/src/__init__.md` |
| `tests/runtime/test_queue.py` | `docs/zh-CN/tests/runtime/test_queue.md` |
| `demo/demo_graph.py` | `docs/zh-CN/demo/demo_graph.md` |

### 镜像文档的 H1 标题规范（本项目，覆盖通用默认）

> 通用 `_subagent-writing.md` 的「标题（H1）规范」要求 H1 = 源码相对**项目根**路径。本项目照此执行，**必须带 `src/celestialflow/` 前缀**（不要写成 `# node/core_node.py` 这种相对映射根的短路径）。

| 源码文件 | 正确的 H1 |
|---------|-----------|
| `src/celestialflow/runtime/util_errors.py` | `# src/celestialflow/runtime/util_errors.py` |
| `src/celestialflow/node/core_node.py` | `# src/celestialflow/node/core_node.py` |
| `src/celestialflow/__init__.py` | `# src/celestialflow/__init__.py` |
| `tests/runtime/test_queue.py` | `# tests/runtime/test_queue.py` |
| `tests/conftest.py` | `# tests/conftest.py` |
| `bench/bench_observer.py` | `# bench/bench_observer.py` |
| `demo/demo_graph.py` | `# demo/demo_graph.py` |

- **禁止**：类名（`# TaskMetrics`）、中文标题（`# 任务图测试 (test_graph.py)`）、短路径（`# node/core_node.py`）、后缀/别名。
- **例外**：`docs/zh-CN/bench/README.md`、`docs/zh-CN/demo/README.md`、`docs/zh-CN/tests/README.md`、`docs/zh-CN/other/*` 等无 1:1 源码的总览文档保留人类可读标题。
- **存量策略**：本区域所有镜像文档的 H1 一律纠正（不只改内容有变的）；仅改 H1 也需刷新 `最后更新日期`。

如果项目里已经存在旧版但不镜像的中文文档路径，优先以"镜像路径"作为目标；必要时说明发现了旧路径遗留问题。
