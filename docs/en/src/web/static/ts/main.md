# main.ts

The main page entry point, responsible for initialization, event binding, and unified data refresh scheduling.

## Responsibilities

- Loads configuration and starts polling after DOMContentLoaded
- Binds UI events for refresh interval selection, theme toggle, and tab switching
- Fetches all data in parallel via `refreshAll()`, triggering module rendering as needed

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `refreshRate` | `number` | Current refresh interval (milliseconds), default 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | Timer handle |

## Initialization Flow

```
DOMContentLoaded
  └─ loadWebConfig()        Load config from /api/pull_config
  └─ applyConfig()          Apply theme, refresh interval, dashboard layout
  └─ Event binding
      ├─ refreshSelect      Refresh interval change → reset timer + save config
      ├─ themeToggleBtn     Theme toggle → rebuild line chart + save config
      └─ tabButtons         Tab switching
  └─ initSortableDashboard()  Initialize stage card drag-and-drop
  └─ refreshAll()             Execute one immediate refresh
  └─ initChart()              Initialize line chart instance
  └─ setInterval(refreshAll)  Start periodic polling
```

## Core Functions

### `refreshAll()`

The main refresh function that coordinates all data updates and UI rendering.

**Flow:**

1. Calls all `load*()` functions in parallel to fetch the latest data; each function returns a `boolean` indicating whether data changed
2. Groups by data domain and only calls the corresponding render function when data has changed

**Change Detection and Render Mapping:**

| Change Condition | Triggered Render |
|-----------------|-----------------|
| `statusesChanged \|\| structureChanged` | `renderMermaidStructure()` |
| `topologyChanged` | `renderTopologyInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

## Cross-Module Dependencies

`main.ts` depends on global functions and variables exposed by other modules (availability ensured by `<script>` tag loading order):

- **web_config.ts** -- `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** -- `loadHistories`, `nodeHistories`, `initChart`, `updateChartData`, `updateChartTheme`
- **task_statuses.ts** -- `loadStatuses`, `nodeStatuses`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** -- `loadStructure`, `structureData`, `renderMermaidStructure`
- **task_errors.ts** -- `loadErrors`, `errors`, `renderErrors`, `populateNodeFilter`
- **task_topology.ts** -- `loadTopology`, `topologyData`, `renderTopologyInfo`
- **task_summary.ts** -- `loadSummary`, `summaryData`, `renderSummary`
- **task_injection.ts** -- `renderNodeList`
- **utils.ts** -- `toggleDarkTheme`, `switchToErrorsTab`
