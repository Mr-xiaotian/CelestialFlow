# task_summary.ts

> 📅 Last updated: 2026/04/22

Manages the loading of overall statistics data and rendering of the summary panel.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `summaryData` | `Record<string, any>` | Aggregated statistics data fetched from the backend |
| `summaryRev` | `number` | Version number from the last fetch, used for incremental fetching (`known_rev`) |

## Functions

### `loadSummary()`

Asynchronously fetches aggregated data from `GET /api/pull_summary?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `summaryData` and `summaryRev`, returning `true`.

---

### `renderSummary()`

Updates the statistics values from `summaryData` to the respective DOM elements in the `#summary-card` panel.

**Display Fields:**

| `summaryData` Field | DOM Element | Description |
|--------------------|-------------|-------------|
| `total_succeeded` | `#total-succeeded` | Total successful tasks |
| `total_pending` | `#total-pending` | Total pending tasks |
| `total_failed` | `#total-failed` | Total failed tasks |
| `total_duplicated` | `#total-duplicated` | Total duplicated tasks |
| `total_nodes` | `#total-nodes` | Active node count |
| `total_remain` | `#total-remain` | Total remaining time (formatted via `formatDuration()`) |

When `total_failed > 0`, the `error-clickable` style is added to `#total-failed`; clicking calls `switchToErrorsTab()` (defined in `utils.ts`, without presetting a stage filter) to navigate to the error log page.
