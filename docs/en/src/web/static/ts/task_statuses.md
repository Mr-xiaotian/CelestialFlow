# task_statuses.ts

Manages the loading of per-stage runtime status data and rendering of dashboard status cards.

## Type Definitions

```ts
type NodeStatus = {
  status: number;            // 0=not running, 1=running, 2=stopped
  tasks_processed: number;   // Number of processed tasks
  tasks_pending: number;     // Number of pending tasks
  tasks_successed: number;   // Cumulative success count
  add_tasks_successed: number; // New successes in this cycle
  add_tasks_pending: number;
  tasks_failed: number;
  add_tasks_failed: number;
  tasks_duplicated: number;
  add_tasks_duplicated: number;
  stage_mode: string;        // serial / thread
  execution_mode: string;    // serial / thread / process / async
  start_time: number;        // Unix timestamp (seconds)
  elapsed_time: number;      // Elapsed seconds
  remaining_time: number;    // Estimated remaining seconds
  task_avg_time: string;     // Average task duration string
};
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `nodeStatuses` | `Record<string, NodeStatus>` | Current status of all stages |
| `statusRev` | `number` | Version number from the last fetch, used for incremental fetching (`known_rev`) |
| `draggingNodeName` | `string \| null` | Name of the stage currently being dragged; skipped during rendering |

## Functions

### `loadStatuses()`

Asynchronously fetches stage status from `GET /api/pull_status?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `nodeStatuses` and `statusRev`, returning `true`.

---

### `initSortableDashboard()`

Initializes drag-and-drop sorting for stage cards (Sortable.js). Skips initialization on mobile devices.

Records `draggingNodeName` during drag operations to prevent `renderDashboard()` from redrawing the card being dragged, which would cause position jumps.

---

### `renderDashboard()`

Iterates over `nodeStatuses`, generating a status card for each stage and inserting it into `#dashboard-grid`.

**Card Contents:**
- Stage name + status badge (not running / running / stopped)
- Statistics: successes, pending, error count (clickable for navigation), duplicates, stage mode, execution mode
- Start time
- Task completion rate progress bar (with elapsed/remaining time, average duration, percentage)

Error numbers have the `error-clickable` style; clicking calls `switchToErrorsTab(node)` (defined in `utils.ts`) to navigate and preset the filter.

## Badge Status Mapping

| `status` Value | CSS Class | Text |
|----------------|-----------|------|
| `0` | `badge-inactive` | Not Running |
| `1` | `badge-running` | Running |
| `2` | `badge-completed` | Stopped |
