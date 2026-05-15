# task_history.ts

> 📅 Last Updated: 2026/05/15

Manages loading of node task processing history data and initialization/updating of line charts.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `nodeHistories` | `Record<string, NodeHistory>` | Per-node history data, fetched from backend |
| `progressChart` | `any` | Chart.js instance |
| `hiddenNodes` | `Set<string>` | Set of hidden nodes in the line chart, persisted to localStorage |
| `historyRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |

## Type Definitions

```ts
type NodeHistory = Array<{ timestamp: number; tasks_processed: number }>;
```

## Functions

### `loadHistories()`

Asynchronously fetches history data from `GET /api/pull_history?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `nodeHistories` and `historyRev`, and returns `true`.

---

### `initChart()`

Initializes (or rebuilds) the Chart.js line chart instance.

- If an instance already exists, calls `destroy()` first to tear it down
- Sets text color, grid color, and axis color based on the current theme (`dark-theme` CSS class)
- Configures legend click events: clicking a legend item toggles node visibility and syncs to localStorage

**The chart instance needs to be rebuilt on theme switch**, so `main.ts` calls `updateChartTheme()` after theme switching to update colors.

---

### `updateChartTheme()`

Updates the line chart's color scheme (text color, grid line color, axis color) without destroying and rebuilding the instance. Called after theme switching.

---

### `updateChartData()`

Writes `nodeHistories` data to the line chart and refreshes it.

1. Calls `extractProgressData(nodeHistories)` to convert to `{x, y}` coordinate points
2. Generates a dataset for each node, with colors assigned by `getColor(index)` and `hidden` state determined by `hiddenNodes`
3. Uses the first node's timestamp sequence to generate X-axis labels (local time strings); returns early if no node data exists
4. Calls `progressChart.update()` to redraw

## Data Flow

```
/api/pull_history
  └─ { "node_tag": [{timestamp, tasks_processed}, ...], ... }
        └─ loadHistories() → nodeHistories
              └─ extractProgressData() → {x, y}[] per node
                    └─ updateChartData() → Chart.js redraw
```
