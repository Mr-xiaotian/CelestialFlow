# dashboard_history.ts

> 📅 Last Updated: 2026/05/28

Manages the maintenance of per-node multi-metric history data and the initialization/redrawing of line charts. History data is accumulated entirely on the frontend via state snapshots.

## Type Definitions

```ts
/** History metric key fields available for chart display switching */
type HistoryMetricKey =
  | "tasks_processed"
  | "tasks_succeeded"
  | "tasks_failed"
  | "tasks_duplicated"
  | "tasks_pending"
  | "delta_tasks_processed"
  | "delta_tasks_succeeded"
  | "delta_tasks_failed"
  | "delta_tasks_duplicated";

/** A single node's history sample point at a given time */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `nodeHistories` | `Record<string, NodeHistory>` | Locally maintained history data sequences for each node |
| `progressChart` | `any` | Chart.js instance |
| `hiddenNodes` | `Set<string>` | Set of hidden nodes in the line chart, persisted to localStorage |
| `currentHistoryMetric` | `HistoryMetricKey` | Current metric displayed on the chart, defaults to `tasks_processed` |
| `metricDots` | `NodeListOf<HTMLLabelElement>` | All `.metric-dot` label elements, used for switching metric display |

## Helper Functions

### `getColor(index)`

Returns a predefined theme color based on index (read from CSS variables), used to differentiate lines for different nodes.

| Index | CSS Variable | Description |
|-------|-------------|-------------|
| 0 | `--cornflower-500` | Cornflower blue |
| 1 | `--jade-500` | Jade green |
| 2 | `--marigold-500` | Marigold yellow |
| 3 | `--crimson-500` | Crimson |
| 4 | `--violet-500` | Violet |
| 5+ | Cyclic modulo, 9-color pool | — |

### `getHistoryMetricLabelKey(metric)`

Maps `HistoryMetricKey` to an i18n translation key.

| Input | Output |
|-------|--------|
| `tasks_processed` | `chart.metric.processed` |
| `tasks_succeeded` | `chart.metric.succeeded` |
| `tasks_failed` | `chart.metric.failed` |
| `tasks_duplicated` | `chart.metric.duplicated` |
| `tasks_pending` | `chart.metric.pending` |
| `delta_tasks_processed` | `chart.metric.deltaProcessed` |
| `delta_tasks_succeeded` | `chart.metric.deltaSucceeded` |
| `delta_tasks_failed` | `chart.metric.deltaFailed` |
| `delta_tasks_duplicated` | `chart.metric.deltaDuplicated` |

### `updateHistoryMetricButtons()`

Iterates over `metricDots`, adding the `.active` class to the matching `<label>` based on `currentHistoryMetric`, and removing it from others.

### `updateChartAxisLabels()`

Updates the line chart X/Y axis title text, mapping them to the current language's "Time" and the corresponding metric name respectively.

---

## Core Logic Functions

### `initChart()`

Initializes (or rebuilds) the Chart.js line chart instance.

- If an instance already exists, calls `destroy()` first
- Calls `getChartThemeColors()` to read the current theme's text color, grid color, and axis color
- Configures legend click events: toggle node visibility and sync to localStorage
- **Does not use `animation`, disables transition animations to improve real-time refresh performance**

### `updateChartTheme()`

Updates the line chart's color scheme (text color, grid line color, axis color). Called after theme switching without rebuilding the instance.

### `updateChartData()`

Writes the corresponding metric data from `nodeHistories` into the line chart based on `currentHistoryMetric` and refreshes it.

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)`

Core logic: Appends history points based on the latest status snapshot.

- **Reset Detection**: If a node's `start_time` changes (restart) or `tasks_processed` regresses (rollback), clears that node's history.
- **Deduplication**: If the timestamp is the same, updates the last point; otherwise appends a new point.
- All modifications are constrained by `getCurrentHistoryLimit()` trimming.

### `extractProgressData(histories, metric)`

Maps locally maintained `nodeHistories` into Chart.js-compatible `{x, y}` coordinate point arrays.

- The `metric` parameter determines which metric to extract (e.g., `tasks_succeeded`, `tasks_failed`, etc.).
- **Delta Mode**: When `metric` starts with `delta_` (e.g., `delta_tasks_processed`), converts cumulative values into differential rate of change (`dy/dt`).
  - Formula: `dy = point[sourceMetric] - prev[sourceMetric]`, `dt = point.timestamp - prev.timestamp`
  - The first point is forced to return `y = 0` (no previous point to calculate the difference)
  - Used to display the trend of change rather than absolute cumulative values

### `trimNodeHistories()`

Trims the locally maintained history point count based on `webConfig.historyLimit`, ensuring performance. Returns a boolean indicating whether history data changed.

### `getCurrentHistoryLimit()`

Gets the current history curve retention point limit. Prioritizes `webConfig?.historyLimit`, defaults to `20` if invalid.

### `getChartThemeColors()`

Reads chart text, grid, and border colors from CSS variables for the current theme (dark/light).

| Theme | Text Color | Grid Color | Border Color |
|-------|-----------|------------|--------------|
| Light | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| Dark | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## Metric Switcher (Module-Level Auto-Execute)

```ts
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // Module-level immediate execution
```

`initHistoryMetricSwitcher()` is automatically called at module scope at the top of `dashboard_history.js`, **not actively called by `main.js`**. It is responsible for:
1. Syncing `metricDots` button active styles
2. Binding click events to switch `currentHistoryMetric`, then updating axis titles and redrawing

## Data Flow

```
GET /api/pull_status
  └─ { timestamp, data: { node: NodeStatus } }
        └─ appendStatusSnapshotToHistory() -> nodeHistories
              └─ updateChartData(currentHistoryMetric) -> Chart.js redraw
```

## Usage Example

### Manually Calling Chart Initialization/Update

The following example shows how to manually operate the chart in the browser console or a custom script:

```typescript
// Assume the page has loaded and global variables are available

// 1. Manually initialize the chart (if not already initialized)
initChart();
console.log("Chart initialized");

// 2. Manually construct a history data point and append it
const timestamp = Date.now() / 1000;  // Current timestamp (seconds)
const statuses: Record<string, NodeStatus> = {
    "Processor": {
        status: 1,
        tasks_processed: 150,
        tasks_succeeded: 145,
        tasks_failed: 3,
        tasks_duplicated: 2,
        tasks_pending: 10,
        stage_mode: "thread",
        execution_mode: "thread",
        start_time: timestamp - 300,
        elapsed_time: 300,
        remaining_time: 20,
        task_avg_time: "2.00s/it",
    },
    "Validator": {
        status: 1,
        tasks_processed: 80,
        tasks_succeeded: 78,
        tasks_failed: 1,
        tasks_duplicated: 1,
        tasks_pending: 5,
        stage_mode: "serial",
        execution_mode: "serial",
        start_time: timestamp - 250,
        elapsed_time: 250,
        remaining_time: 15,
        task_avg_time: "3.12s/it",
    },
};

// 3. Append status snapshot to history sequence
// appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses)
// This automatically updates the nodeHistories global variable

// 4. Switch the currently displayed metric
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // Refresh chart

// 5. Switch metrics (simulate clicking different metric buttons)
function switchMetric(metric: HistoryMetricKey) {
    // currentHistoryMetric = metric;
    // updateHistoryMetricButtons();
    // updateChartData();
    console.log(`Switched to metric: ${metric}`);
}

switchMetric("tasks_failed");  // Show failure trend
switchMetric("tasks_pending"); // Show pending queue trend

// 6. Manually trim history data (force keep last N entries)
// webConfig.historyLimit = 10;
// const changed = trimNodeHistories();
// if (changed) updateChartData();

// 7. Update chart colors after theme switch
// updateChartTheme();
```

### Constructing History Data and Rendering Directly

```typescript
// Directly manually construct complete nodeHistories data
const mockHistory: Record<string, NodeHistory> = {
    "Processor": [
        { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90 },
        { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75 },
        { timestamp: 1010, tasks_processed: 40, tasks_succeeded: 37, tasks_failed: 2, tasks_duplicated: 1, tasks_pending: 60 },
        { timestamp: 1015, tasks_processed: 55, tasks_succeeded: 51, tasks_failed: 2, tasks_duplicated: 2, tasks_pending: 45 },
        { timestamp: 1020, tasks_processed: 70, tasks_succeeded: 65, tasks_failed: 3, tasks_duplicated: 2, tasks_pending: 30 },
    ],
};

// nodeHistories = mockHistory;
// updateChartData();  // Render to line chart

// Use getColor to get the node's line color
// const color = getColor(0);  // 1st node, cornflower blue
```
