# Subagent: Web/Static (TypeScript + CSS)

> 覆盖 `src/celestialflow/web/static/ts/` 和 `src/celestialflow/web/static/css/` 的中文文档。
>
> 开始工作前，请先阅读同目录下的 `_subagent-base.md`、`_subagent-audit.md`、`_subagent-writing.md`，再结合本文件和主 agent 提供的文件清单执行审计。

## 文件清单

> 具体的代码→文档对照清单由主 agent 在委派时提供。子代理以主 agent 提供的清单为准。

## 区域特化陷阱（高频错误）

| 陷阱 | 典型表现 | 排查方法 |
|------|---------|---------|
| 🔴 虚构导出函数 | 文档写了 `loadSummary()`、`renderLocalTime()`、`initSortableDashboard()`，源码中不存在 | `grep "export function\|function "` 对照文档 |
| 🔴 遗漏新增函数 | 源码新增 `getNodeShape()`、`renderLabelWithTooltip()`、`calcRemainTime()` 等，文档未提及 | 同上 |
| 🔴 函数归属错误 | 函数实际在 `main.ts` 中，文档错误记在 `utils.ts` 下 | 用 `grep` 确认函数定义文件 |
| 🟠 CSS 类名/选择器漂移 | `.sortable-dragging`/`.sortable-ghost` 源码已删除、`.history-metric-switcher` → `.metric-indicators` | `grep` CSS 类选择器 vs 文档 |
| 🟠 类型定义过期 | `structureData: any[]` → `StructureGraph`、`ErrorData` 字段名变更 | 对照 `.d.ts` 和 TS 源码中的 interface/type |
| 🟠 文件拆分未同步 | `injection.css` 拆为 4 个文件，但只有 1 个 `injection.md` | `find_path` 对比 CSS 文件数 vs 文档数 |
| 🟡 API 端点虚构 | 文档提到 `/api/pull_summary` 等不存在的端点 | grep TS 中的 `fetch(` 或 API 路径常量 |
| 🟡 模块交互描述错误 | `refreshAll()` 调用 5 个刷新 → 实际 4 个并行 | 阅读 `main.ts` 中的 `refreshAll` 实现 |
| 🟡 存储机制描述错误 | 文档说 localStorage → 源码用内存变量 | 确认数据持久化方式 |
| 🟡 配置结构过期 | `WebConfig` 从平铺 → 分组（`global`/`dashboard`/`errors`/`injection`） | 对照 `web_config.ts` 中的 interface 定义 |

### 区域差异化写作规则

**TypeScript 文档：**
- 重点说明：模块职责、导出函数/变量、DOM 操作目标元素、与后端 API 的交互、事件绑定
- 用**表格**列出所有导出函数（函数名 | 参数 | 返回值 | 用途）
- 用 `sequenceDiagram` 展示与后端 API 的交互流程
- 用 `flowchart` 展示模块间数据流（如 `main.ts` → 各 dashboard 模块的分发）
- `globals.d.ts`：说明全局类型声明，重点列出 Chart.js、Sortable.js 等第三方库的类型定义
- `i18n.ts`：说明国际化机制和翻译键结构
- `web_config.ts`：说明配置结构和类型定义，注意分组后的访问方式

**CSS 文档：**
- 重点说明：样式作用域、关键 class/选择器、布局策略（flexbox/grid）、与对应 TS 模块的关系
- `_colors.css`：说明 CSS 变量体系和颜色命名规范
- `base.css`：说明全局基础样式和重置规则
- 各 `dashboard_*.css`：说明对应 dashboard 面板的布局和样式约定
- **injection CSS 拆分检查**：确认 `injection.css` 是否已拆为 4 个独立文件。如果是：
  - 为 `injection_editor.css`、`injection_layout.css`、`injection_nodes.css`、`injection_preview.css` 各创建独立文档
  - 在原有的 `injection.md` 中标注"已拆分"，列出 4 个子文件及对应职责
