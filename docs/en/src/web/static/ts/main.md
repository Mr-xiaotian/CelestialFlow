# main.ts

> 📅 Last Updated: 2026/05/15

The main page entry point, responsible for initialization, event binding, and unified data refresh scheduling.

## Responsibilities

- Load configuration and start polling after DOMContentLoaded
- Bind UI events for settings panel, refresh interval, history length, theme switching, tab switching, etc.
- Fetch all data in parallel via `refreshAll()` and trigger rendering for each module as needed

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `refreshRate` | `number` | Current refresh interval (milliseconds), default 5000 |
| `refreshIntervalId` | `ReturnType<typeof setInterval> \| null` | Timer handle |

## DOM Element References

| Variable | Selector | Description |
|----------|----------|-------------|
| `refreshSelect` | `#refresh-interval` | Refresh interval dropdown |
| `historyLimitSelect` | `#history-limit` | History length dropdown |
| `settingsBtn` | `#settings-btn` | Settings gear button |
| `settingsPanel` | `#settings-panel` | Settings floating panel |
| `settingsClose` | `#settings-close` | Settings panel close button |
| `themeToggleBtn` | `#theme-toggle` | Theme toggle button |
| `tabButtons` | `.tab-btn` | Tab button list |
| `tabContents` | `.tab-content` | Tab content list |

## Initialization Flow

```
DOMContentLoaded
  └─ loadWebConfig()        Load config from /api/pull_config
  └─ applyConfig()          Apply theme, refresh interval, history length, dashboard layout
  └─ Event binding
      ├─ settingsBtn        Click gear button: toggle settings panel visibility
      ├─ settingsClose      Click close button: hide settings panel
      ├─ document click     Click outside: auto-close settings panel
      ├─ refreshSelect      Refresh interval change → reset timer + save config
      ├─ historyLimitSelect History length change → save config (takes effect on next backend snapshot)
      ├─ themeToggleBtn     Theme toggle → re-render charts + save config
      └─ tabButtons         Tab switching
  └─ initSortableDashboard()  Initialize node card drag-and-drop
  └─ refreshAll()             Execute one refresh immediately
  └─ initChart()              Initialize line chart instance
  └─ setInterval(refreshAll)  Start periodic polling
```

## Core Functions

### `refreshAll()`

The main refresh function that coordinates all data updates and UI rendering.

**Flow:**

1. Call all `load*()` functions in parallel to fetch the latest data; each returns a `boolean` indicating whether data changed
2. Group by data domain and only call the corresponding render function when data has changed

**Change Detection and Render Mapping:**

| Change Condition | Triggered Render |
|------------------|-----------------|
| `statusesChanged \|\| structureChanged` | `renderMermaidStructure()` |
| `analysisChanged` | `renderAnalysisInfo()` |
| `summaryChanged` | `renderSummary()` |
| `historiesChanged` | `updateChartData()` |
| `statusesChanged` | `renderDashboard()` / `populateNodeFilter()` / `renderNodeList()` |
| `errorsChanged` | `renderErrors()` |

## Cross-module Dependencies

`main.ts` depends on global functions and variables exposed by other modules (availability ensured by `<script>` tag load order):

- **web_config.ts** — `loadWebConfig`, `saveWebConfig`, `applyConfig`, `webConfig`, `applyDashboardLayout`
- **task_history.ts** — `loadHistories`, `nodeHistories`, `initChart`, `updateChartData`, `updateChartTheme`
- **task_statuses.ts** — `loadStatuses`, `nodeStatuses`, `renderDashboard`, `initSortableDashboard`
- **task_structure.ts** — `loadStructure`, `structureData`, `renderMermaidStructure`
- **task_errors.ts** — `loadErrors`, `errors`, `renderErrors`, `populateNodeFilter`
- **task_analysis.ts** — `loadAnalysis`, `analysisData`, `renderAnalysisInfo`
- **task_summary.ts** — `loadSummary`, `summaryData`, `renderSummary`
- **task_injection.ts** — `renderNodeList`
- **utils.ts** — `toggleDarkTheme`, `switchToErrorsTab`
