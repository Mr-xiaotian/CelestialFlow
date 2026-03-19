# main.ts

页面主入口，负责初始化、事件绑定和统一数据刷新调度。

## 职责

- DOMContentLoaded 后加载配置并启动轮询
- 绑定刷新间隔选择、主题切换、标签页切换等 UI 事件
- 通过 `refreshAll()` 并行拉取所有数据，按需触发各模块渲染

## 全局变量

| 变量 | 类型 | 说明 |
|------|------|------|
| `refreshRate` | `number` | 当前刷新间隔（毫秒），默认 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | 定时器句柄 |

## 初始化流程

```
DOMContentLoaded
  └─ loadWebConfig()        从 /api/pull_config 加载配置
  └─ applyConfig()          应用主题、刷新间隔、仪表盘布局
  └─ 事件绑定
      ├─ refreshSelect      刷新间隔变更 → 重置定时器 + 保存配置
      ├─ themeToggleBtn     主题切换 → 重建折线图 + 保存配置
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

1. 并行调用所有 `load*()` 函数拉取最新数据
2. 将各数据序列化为 JSON 字符串，与上次对比判断是否变化
3. 按数据域分组，仅在数据发生变化时调用对应渲染函数

**变化检测与渲染映射：**

| 变化条件 | 触发渲染 |
|----------|---------|
| `statusesChanged \|\| structureChanged` | `renderMermaidFromTaskStructure()` |
| `topologyChanged` | `renderTopologyInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

> 注意：`statusesChanged` 被检查两次（与 `structureChanged` 组合，以及单独检查），`previousNodeStatusesJSON` 在第一次命中时更新。

## 跨模块依赖

`main.ts` 依赖其他模块暴露的全局函数和变量（通过 `<script>` 标签加载顺序确保可用）：

- **web_config.ts** — `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** — `loadHistories`, `nodeHistories`, `previousNodeHistoriesJSON`, `initChart`, `updateChartData`
- **task_statuses.ts** — `loadStatuses`, `nodeStatuses`, `previousNodeStatusesJSON`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** — `loadStructure`, `structureData`, `previousStructureDataJSON`, `renderMermaidFromTaskStructure`
- **task_errors.ts** — `loadErrors`, `errors`, `previousErrorsJSON`, `renderErrors`, `populateNodeFilter`
- **task_topology.ts** — `loadTopology`, `topologyData`, `previousTopologyDataJSON`, `renderTopologyInfo`
- **task_summary.ts** — `loadSummary`, `summaryData`, `previousSummaryDataJSON`, `renderSummary`
- **task_injection.ts** — `renderNodeList`
- **utils.ts** — `toggleDarkTheme`
