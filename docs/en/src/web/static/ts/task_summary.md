# task_summary.ts

> 📅 Last Updated: 2026/04/22

Manages loading of overall statistics data and rendering of the summary panel.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `summaryData` | `Record<string, any>` | Aggregated statistics data, fetched from backend |
| `summaryRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |

## Functions

### `loadSummary()`

Asynchronously fetches summary data from `GET /api/pull_summary?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `summaryData` and `summaryRev`, and returns `true`.

---

### `renderSummary()`

Updates the statistics values from `summaryData` into the various DOM elements within the `#summary-card` panel.

**Displayed fields:**

| `summaryData` Field | DOM Element | Description |
|--------------------|-------------|-------------|
| `total_succeeded` | `#total-succeeded` | Total succeeded task count |
| `total_pending` | `#total-pending` | Total pending task count |
| `total_failed` | `#total-failed` | Total failed task count |
| `total_duplicated` | `#total-duplicated` | Total duplicated task count |
| `total_nodes` | `#total-nodes` | Active node count |
| `total_remain` | `#total-remain` | Total remaining time (formatted via `formatDuration()`) |

When `total_failed > 0`, the `error-clickable` style is added to `#total-failed`. Clicking calls `switchToErrorsTab()` (defined in `utils.ts`, without presetting the node filter) to navigate to the error log page.
