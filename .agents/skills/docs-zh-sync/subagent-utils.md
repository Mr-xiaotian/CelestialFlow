# Subagent: Utils + Package Entry (Python)

> 覆盖 `src/celestialflow/__init__.py` 与 `src/celestialflow/utils/` 下的中文文档。
>
> 开始工作前，请按顺序阅读：
> 1. `~/.agents/skills/docs-zh-sync/_subagent-base.md`（通用规则、输出格式）
> 2. `~/.agents/skills/docs-zh-sync/_subagent-audit.md`（通用审计清单）
> 3. `~/.agents/skills/docs-zh-sync/_subagent-writing.md`（通用写作规范）
> 4. 项目内 `.agents/skills/docs-zh-sync/_subagent-base.md`（项目专属路径映射）
> 5. 本文件
>
> 再结合主 agent 提供的文件清单执行审计。

## 文件清单

> 具体的代码→文档对照清单由主 agent 在委派时提供。子代理以主 agent 提供的清单为准。

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 顶层导出过期 | `__init__.py` 文档仍列出已删除或已迁出的符号 | 对照 `__all__` 与 import 语句 |
| 🔴 工具函数签名过期 | 文档参数名、返回值、异常说明与源码不一致 | 逐函数对照签名与 docstring |
| 🟠 模块职责描述错误 | `utils/` 文档把函数写成核心流程节点 | 结合调用方判断真实职责 |
| 🟠 示例代码失效 | 文档示例仍引用旧路径、旧构造方式、旧导入 | grep 示例中的类名/函数名/路径 |
| 🟡 返回值描述漂移 | 文档仍写旧 tuple/dict 结构 | 对照函数返回注解与实际 return |
| 🟢 虚构功能 | 文档提到源码中不存在的辅助函数或配置项 | grep 全量核对 |

### 区域差异化写作规则

- **`src/celestialflow/__init__.py`**：列出完整 `__all__` 列表，按子模块分组。提供 top-level import 示例。
- **`utils/__init__.py`**：列出工具模块的全部导出符号。
- **`util_*.py`**：逐函数说明用途、参数、返回值。建议用表格（函数名 | 用途 | 关键参数 | 返回值）。
- **示例代码**：所有导入路径、函数名、构造方式必须与当前源码一致，不保留已迁出模块的旧示例。
