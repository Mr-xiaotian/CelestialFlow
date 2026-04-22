# task_history.ts

Manages the loading of per-stage task processing history data and the initialization and updating of line charts.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `nodeHistories` | `Record<string, NodeHistory>` | Per-stage history data fetched from the backend |
| `progressChart` | `any` | Chart.js instance |
| `hiddenNodes` | `Set<string>` | Set of stages hidden in the line chart, persisted to localStorage |
| `historyRev` | `number` | Version number from the last fetch, used for incremental fetching (`known_rev`) |

## Type Definitions

```ts
type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;
```

## Functions

### `loadHistories()`

Asynchronously fetches history data from `GET /api/pull_history?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `nodeHistories` and `historyRev`, returning `true`.

---

### `initChart()`

Initializes (or rebuilds) the Chart.js line chart instance.

- If an instance already exists, calls `destroy()` to dispose of it first
- Sets text color, grid color, and axis line color based on the current theme (`dark-theme` CSS class)
- Configures legend click events: clicking a legend item toggles stage visibility and syncs the state to localStorage

**The chart instance must be rebuilt on theme switch**, so `main.ts` calls `updateChartTheme()` after theme changes to update colors.

---

### `updateChartTheme()`

Updates the line chart color scheme (text color, grid line color, axis line color) without destroying and rebuilding the instance. Called after theme switches.

---

### `updateChartData()`

Writes `nodeHistories` data to the line chart and refreshes it.

1. Calls `extractProgressData(nodeHistories)` to convert to `{x, y}` coordinate points
2. Generates a dataset for each stage; colors are assigned by `getColor(index)`, `hidden` state is determined by `hiddenNodes`
3. Uses the first stage's timestamp sequence to generate X-axis labels (local time strings)
4. Calls `progressChart.update()` to redraw

## Data Flow

```
/api/pull_history
  └─ { "node_tag": [{timestamp, tasks_processed}, ...], ... }
        └─ loadHistories() → nodeHistories
              └─ extractProgressData() → {x, y}[] per node
                    └─ updateChartData() → Chart.js redraw
```
