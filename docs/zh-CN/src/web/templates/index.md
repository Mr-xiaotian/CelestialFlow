# index.html

> 📅 最后更新日期: 2026/05/15

Web UI 的 Jinja2 模板文件，定义了监控系统的完整页面结构。

## 整体布局

页面分为三个主要区域：

```
<header>  — 顶部控制栏（设置面板、主题切换）
<main>
  ├─ .tabs          — 标签页导航
  ├─ #dashboard     — 仪表盘（三栏布局）
  ├─ #errors        — 错误日志
  └─ #task-injection — 任务注入
```

## Header 控制栏

| 元素 | ID / Class | 说明 |
|------|-----------|------|
| 设置按钮 | `#settings-btn` / `.btn-settings` | 齿轮 SVG 图标，点击打开设置面板 |
| 设置面板 | `#settings-panel` / `.settings-panel` | 悬浮面板，包含刷新间隔和历史长度两项设置 |
| 关闭按钮 | `#settings-close` / `.settings-close` | 设置面板内的关闭按钮 |
| 刷新间隔 | `#refresh-interval` | 下拉框，可选 1s/2s/5s/10s/30s |
| 历史长度 | `#history-limit` | 下拉框，可选 10/20/50/100 |
| 主题切换 | `#theme-toggle` | 明暗模式切换按钮 |

设置面板默认隐藏（`hidden` 类），点击齿轮按钮切换显示，点击面板外区域或关闭按钮隐藏。

## 标签页

| Tab ID | 按钮 `data-tab` | 说明 |
|--------|----------------|------|
| `#dashboard` | `dashboard` | 实时任务图监控面板 |
| `#errors` | `errors` | 错误日志列表 |
| `#task-injection` | `task-injection` | 任务注入 |

## Dashboard 三栏结构

### 左栏 `.left-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 任务结构图 | `.mermaid-card` | Mermaid 流程图容器 `#mermaid-container` |
| 图分析信息 | `.analysis-card` | 显示 DAG 状态、调度模式、层级数 |

### 中栏 `.middle-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 节点运行状态 | `.status-card` | 动态生成的节点状态卡片网格 `#dashboard-grid` |

### 右栏 `.right-panel`

| 卡片 | Class | 说明 |
|------|-------|------|
| 节点完成走向 | `.progress-card` | Chart.js 折线图 `<canvas id="node-progress-chart">` |
| 总体状态摘要 | `.summary-card` | 6 格统计：成功/等待/错误/重复/活动节点/剩余时间 |

> 卡片的实际栏位分配和显示/隐藏由 `web_config.ts` 的 `applyDashboardLayout()` 动态控制，初始 HTML 中卡片均设为 `display: none`。

## 错误日志面板

- 关键词搜索框 `#error-search`
- 节点筛选下拉 `#node-filter`
- 错误表格 `#errors-table`（列：序号 / 错误id / 错误信息 / 节点 / 任务 / 时间）
- 分页控件容器 `#pager-container`

## 任务注入面板

- 节点搜索 `#search-input` + 节点列表 `#node-list`
- 全选/清空按钮
- 已选节点区域 `#selected-section` / `#selected-list`
- 输入方式切换：JSON 文本（`#json-textarea`）/ 文件上传（`#file-input`）
- 插入终止符快捷按钮 `fillTermination()`
- 提交按钮 `#submit-btn` + 状态提示 `#status-message`

## 外部依赖（CDN）

| 库 | 版本 | 用途 |
|----|------|------|
| Chart.js | latest | 折线图 |
| SortableJS | latest | 节点卡片拖拽排序 |
| Mermaid | `^10` (ESM) | 任务图可视化 |

Mermaid 通过 `<script type="module">` 以 ESM 方式加载，并挂载到 `window.mermaid`，供 `task_structure.ts` 调用。

## JS 脚本加载顺序

脚本按以下顺序加载（依赖顺序）：

```html
utils.js          ← 工具函数（无依赖）
web_config.js     ← 依赖 utils（引用 refreshSelect 等 DOM 元素）
task_statuses.js  ← 依赖 utils
task_structure.js ← 依赖 utils, task_statuses（读 nodeStatuses）
task_errors.js    ← 依赖 utils, task_statuses（读 nodeStatuses）
task_analysis.js  ← 依赖 utils
task_summary.js   ← 依赖 utils
task_history.js   ← 依赖 utils（extractProgressData, getColor）
task_injection.js ← 依赖 task_statuses（读 nodeStatuses）, utils
main.js           ← 依赖所有上述模块
```

## CSS 样式引用

```html
css/_colors.css    ← 颜色变量定义
css/base.css       ← 全局样式、主题变量、设置面板样式
css/dashboard.css  ← 仪表盘、卡片、进度条样式
css/errors.css     ← 错误表格、分页样式
css/inject.css     ← 任务注入页面样式
```
