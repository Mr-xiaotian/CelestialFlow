# task_statuses.ts

> 📅 Last Updated: 2026/05/15

Manages loading of per-node running status data and rendering of dashboard status cards.

## Type Definitions

```ts
type NodeStatus = {
  status: number;            // 0=not running, 1=running, 2=stopped
  tasks_processed: number;   // Tasks processed count
  tasks_pending: number;     // Pending tasks count
  tasks_succeeded: number;   // Cumulative succeeded count
  tasks_failed: number;      // Cumulative failed count
  tasks_duplicated: number;  // Cumulative duplicated count
  stage_mode: string;        // serial / thread
  execution_mode: string;    // serial / thread / async
  start_time: number;        // Unix timestamp (seconds)
  elapsed_time: number;      // Elapsed seconds
  remaining_time: number;    // Estimated remaining seconds
  task_avg_time: string;     // Average task duration string
};
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `nodeStatuses` | `Record<string, NodeStatus>` | Current statuses of all nodes |
| `lastNodeStatuses` | `Record<string, NodeStatus>` | Previous status snapshot, used for delta calculation |
| `statusRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |
| `draggingNodeName` | `string \| null` | Currently dragged node name, skipped during rendering |

## Functions

### `loadStatuses()`

Asynchronously fetches node statuses from `GET /api/pull_status?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise saves the current `nodeStatuses` as `lastNodeStatuses`, updates `nodeStatuses` and `statusRev`, and returns `true`.

---

### `initSortableDashboard()`

Initializes node card drag-and-drop sorting (Sortable.js). Skips initialization on mobile devices.

Records `draggingNodeName` during drag to prevent `renderDashboard()` from redrawing the dragged card, which would cause position jumping.

---

### `renderDashboard()`

Iterates over `nodeStatuses`, generating a status card for each node and inserting it into `#dashboard-grid`.

Deltas are calculated via `lastNodeStatuses` (e.g., `data.tasks_succeeded - last.tasks_succeeded`) and displayed as colored small text.

**Card contents:**
- Node name
- Statistics: succeeded, pending, errors (clickable for navigation), duplicated, stage mode, execution mode
- Start time
- Task completion progress bar (four segments: succeeded/errors/duplicated/pending), with elapsed/remaining time, average duration, and percentage

Error numbers have the `error-clickable` style; clicking calls `switchToErrorsTab(node)` (defined in `utils.ts`) to navigate and preset the filter.

## Card Status Styles

| `status` Value | CSS Class | Meaning |
|----------------|-----------|---------|
| `0` | `node-card` | Not running |
| `1` | `node-card status-running` | Running |
| `2` | `node-card status-stopped` | Stopped |
