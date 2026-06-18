# dashboard_history.ts

> 📅 Last Updated: 2026/06/18

Manages the maintenance of per-node multi-metric history data and the initialization/redraw of the line chart. History data is accumulated entirely on the frontend via status snapshots, independent of any dedicated backend API.

## Type Definitions

```typescript
/** Metric field keys available for the history chart */
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

/** A single history sample point for a node at a point in time */
type NodeHistoryPoint = {
  timestamp: number;
  tasks_processed: number;
  tasks_succeeded: number;
  tasks_failed: number;
  tasks_duplicated: number;
  tasks_pending: number;
};

type NodeHistory = NodeHistoryPoint[];

type ThemeColors = {
  text: string;   // Axis and legend text color
  grid: string;   // Grid line color
  border: string; // Axis border color
};
```

## Global Variables

| Variable | Type | Description |
|------|------|------|
| `nodeHistories` | `Record<string, NodeHistory>` | Locally maintained history data series per node |
| `progressChart` | `ChartInstance \| null` | Chart.js line chart instance |
| `hiddenNodes` | `Set<string>` | Set of nodes manually hidden by the user in the legend (retained only during page lifecycle, **not persisted**) |
| `currentHistoryMetric` | `HistoryMetricKey` | The metric currently displayed in the chart, defaults to `"tasks_processed"` |
| `metricDots` | `NodeListOf<HTMLLabelElement>` | All `.metric-dot` label elements, used to switch displayed metrics |

## Helper Functions

### `getColor(index: number): string`

Reads predefined theme colors from CSS variables by index for distinguishing different node lines. 9 colors, cycled via modulo.

| Index | CSS Variable | Description |
|-------|---------|------|
| 0 | `--cornflower-500` | Cornflower blue |
| 1 | `--jade-500` | Jade green |
| 2 | `--marigold-500` | Marigold yellow |
| 3 | `--crimson-500` | Crimson red |
| 4 | `--violet-500` | Violet |
| 5 | `--rose-500` | Rose red |
| 6 | `--jade-400` | Jade green (light) |
| 7 | `--sky-500` | Sky blue |
| 8 | `--amber-500` | Amber orange |

### `getHistoryMetricLabelKey(metric: HistoryMetricKey): string`

Maps a `HistoryMetricKey` to an i18n translation key.

| Input | Output |
|------|------|
| `tasks_processed` | `chart.metric.processed` |
| `tasks_succeeded` | `chart.metric.succeeded` |
| `tasks_failed` | `chart.metric.failed` |
| `tasks_duplicated` | `chart.metric.duplicated` |
| `tasks_pending` | `chart.metric.pending` |
| `delta_tasks_processed` | `chart.metric.deltaProcessed` |
| `delta_tasks_succeeded` | `chart.metric.deltaSucceeded` |
| `delta_tasks_failed` | `chart.metric.deltaFailed` |
| `delta_tasks_duplicated` | `chart.metric.deltaDuplicated` |

### `updateHistoryMetricButtons(): void`

Iterates over `metricDots`, adding the `.active` class to the matching `<label>` based on `currentHistoryMetric`, and removing it from the rest.

### `updateChartAxisLabels(): void`

Updates the line chart X/Y axis title text, mapping them to "Time" and the corresponding metric name in the current language.

---

## Core Logic Functions

### `initChart(): void`

Initializes (or rebuilds) the Chart.js line chart instance.

- If an instance already exists, calls `destroy()` first
- Calls `getChartThemeColors()` to read the current theme's text, grid, and axis colors
- Configures legend click events: toggles node visibility and syncs to the `hiddenNodes` Set
- **Disables animation** (`animation: false`) to improve real-time refresh performance
- Interaction mode is `index`, `intersect: false`

### `updateChartTheme(): void`

Updates the line chart's color scheme (text, grid line, axis colors). Called after theme switching without rebuilding the instance.

### `updateChartData(): void`

Calls `extractProgressData()` based on `currentHistoryMetric` to write corresponding metric data from `nodeHistories` into the line chart and refresh. Syncs `legendItem.hidden` to ensure legend rendering matches `hiddenNodes`.

### `appendStatusSnapshotToHistory(timestamp, statuses, previousStatuses?): boolean`

Core logic: appends a history point based on the latest status snapshot.

- **Reset detection**: If a node's `start_time` changes (restart) or `tasks_processed` regresses (rollback), clears that node's history.
- **Deduplication**: If the timestamp is the same, updates the last point; otherwise appends a new point.
- **Trimming**: All modifications are constrained by `getCurrentHistoryLimit()`.
- **Return value**: `boolean` — whether the history data changed.

### `extractProgressData(histories, metric): Record<string, Array<{x: number; y: number}>>`

Converts the locally maintained `nodeHistories` map into Chart.js-compatible `{x, y}` coordinate point arrays.

- **Cumulative mode**: Reads raw field values from sample points directly.
- **Delta mode**: When `metric` starts with `delta_`, computes the rate per second from differences between adjacent sample points. Forces `y = 0` for the first point.

### `trimNodeHistories(): boolean`

Trims the number of frontend-maintained history points based on `webConfig.dashboard.historyLimit`. Returns a boolean indicating whether the history data changed.

### `getCurrentHistoryLimit(): number`

Gets the current history curve point retention limit. Prefers `webConfig.dashboard.historyLimit`; defaults to `20` when invalid.

### `getChartThemeColors(): ThemeColors`

Reads chart text, grid line, and border colors from CSS variables for the current theme (dark/light).

| Theme | Text Color | Grid Color | Border Color |
|------|--------|--------|--------|
| Light | `--carbon-900` | `--carbon-200` | `--carbon-300` |
| Dark | `--carbon-200` | `--carbon-600` | `--carbon-500` |

---

## Metric Switcher (Module-level Auto-execution)

```typescript
function initHistoryMetricSwitcher() { ... }
initHistoryMetricSwitcher(); // Module-level immediate execution
```

`initHistoryMetricSwitcher()` is automatically invoked in module scope, **not actively called by `main.ts`**. It is responsible for:

1. Syncing `metricDots` button activation styles
2. Binding click events, switching `currentHistoryMetric` then updating axis titles and redrawing

## Data Flow

```mermaid
flowchart LR
    subgraph "dashboard_statuses.ts"
        LS[loadStatuses]
    end
    subgraph "dashboard_history.ts"
        AS[appendStatusSnapshotToHistory]
        NH[nodeHistories]
        EC[extractProgressData]
        UC[updateChartData]
        CH[Chart.js instance]
    end
    LS -->|timestamp + statuses| AS
    AS --> NH
    NH --> EC
    EC -->|{x, y} coordinates| UC
    UC --> CH
```

## Usage Example

```typescript
// Manually construct history data and render
const mockHistory: Record<string, NodeHistory> = {
  "Processor": [
    { timestamp: 1000, tasks_processed: 10, tasks_succeeded: 9, tasks_failed: 1, tasks_duplicated: 0, tasks_pending: 90 },
    { timestamp: 1005, tasks_processed: 25, tasks_succeeded: 23, tasks_failed: 1, tasks_duplicated: 1, tasks_pending: 75 },
  ],
};

// nodeHistories = mockHistory;
// currentHistoryMetric = "tasks_succeeded";
// updateChartData();  // Render to line chart

// Update chart colors after theme switch
// updateChartTheme();

// Manually trim history data
// webConfig.dashboard.historyLimit = 10;
// if (trimNodeHistories()) updateChartData();
```
