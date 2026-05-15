# main.ts

> 📅 最后更新日期: 2026/05/15

页面主入口，负责初始化、事件绑定和统一数据刷新调度。

## 职责

- DOMContentLoaded 后加载配置并启动轮询
- 绑定设置面板、刷新间隔、历史长度、主题切换、标签页切换等 UI 事件
- 通过 `refreshAll()` 并行拉取所有数据，按需触发各模块渲染

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `refreshRate` | `number` | 当前刷新间隔（毫秒），默认 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | 定时器句柄 |

## DOM 元素引用

| 变量 | 选择器 | 说明 |
|------|--------|------|
| `refreshSelect` | `#refresh-interval` | 刷新间隔下拉框 |
| `historyLimitSelect` | `#history-limit` | 历史长度下拉框 |
| `settingsBtn` | `#settings-btn` | 设置齿轮按钮 |
| `settingsPanel` | `#settings-panel` | 设置悬浮面板 |
| `settingsClose` | `#settings-close` | 设置面板关闭按钮 |
| `themeToggleBtn` | `#theme-toggle` | 主题切换按钮 |
| `tabButtons` | `.tab-btn` | 页签按钮列表 |
| `tabContents` | `.tab-content` | 页签内容列表 |

## 初始化流程

```
DOMContentLoaded
  └─ loadWebConfig()        从 /api/pull_config 加载配置
  └─ applyConfig()          应用主题、刷新间隔、历史长度、仪表盘布局
  └─ 事件绑定
      ├─ settingsBtn        点击齿轮按钮：切换设置面板显示/隐藏
      ├─ settingsClose      点击关闭按钮：隐藏设置面板
      ├─ document click     点击页面空白处：自动关闭设置面板
      ├─ refreshSelect      刷新间隔变更 → 重置定时器 + 保存配置
      ├─ historyLimitSelect 历史长度变更 → 保存配置（后端下次快照时生效）
      ├─ themeToggleBtn     主题切换 → 重新渲染图表 + 保存配置
      └─ tabButtons         标签页切换
  └─ initSortableDashboard()  初始化节点卡片拖拽
  └─ refreshAll()             立即执行一次刷新
  └─ initChart()              初始化折线图实例
  └─ setInterval(refreshAll)  启动周期轮询
```

## 核心函数

### `refreshAll()`

主刷新函数，协调所有数据更新和 UI 渲染。

**流程：**

1. 并行调用所有 `load*()` 函数拉取最新数据，各函数返回 `boolean` 表示数据是否变化
2. 按数据域分组，仅在数据发生变化时调用对应渲染函数

**变化检测与渲染映射：**

| 变化条件 | 触发渲染 |
|----------|---------|
| `statusesChanged \|\| structureChanged` | `renderMermaidStructure()` |
| `analysisChanged` | `renderAnalysisInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

## 跨模块依赖

`main.ts` 依赖其他模块暴露的全局函数和变量（通过 `<script>` 标签加载顺序确保可用）：

- **web_config.ts** — `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** — `loadHistories`, `nodeHistories`, `initChart`, `updateChartData`, `updateChartTheme`
- **task_statuses.ts** — `loadStatuses`, `nodeStatuses`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** — `loadStructure`, `structureData`, `renderMermaidStructure`
- **task_errors.ts** — `loadErrors`, `errors`, `renderErrors`, `populateNodeFilter`
- **task_analysis.ts** — `loadAnalysis`, `analysisData`, `renderAnalysisInfo`
- **task_summary.ts** — `loadSummary`, `summaryData`, `renderSummary`
- **task_injection.ts** — `renderNodeList`
- **utils.ts** — `toggleDarkTheme`, `switchToErrorsTab`
