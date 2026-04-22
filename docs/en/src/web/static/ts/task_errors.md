# task_errors.ts

Manages the loading, filtering, pagination, and rendering of error log data.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `errors` | `any[]` | Error record array fetched from the backend |
| `errorsOffset` | `number` | Number of synchronized errors, used for incremental fetching |
| `currentPage` | `number` | Current page number, default 1 |
| `pageSize` | `number` | Records per page, fixed at 10 |

## Functions

### `loadErrors()`

Asynchronously fetches incremental error list from `GET /api/pull_errors?offset=N`, updating `errors`.

- If `data.total < errorsOffset` (error_store has been cleared after server restart), performs a full resync
- New entries are appended to the end of `errors`, returns `true`; returns `false` if no new data

---

### `renderErrors()`

Renders the error table with support for stage filtering and keyword search, sorted by timestamp in descending order.

**Filter Rules:**
- Stage filter: Matches `e.stage === filter`
- Keyword search: Fuzzy matches `e.error_repr` or `e.task_repr` (case-insensitive)

Table columns: error ID, error message, stage, task, time.

---

### `buildPageList(current, total)`

Generates a smart page number array containing the first and last pages, the current page and its surrounding 2 pages, with gaps filled by `"..."`.

---

### `renderPaginationControls(totalPages)`

Renders pagination controls including "Previous" / "Next" buttons and numeric page buttons. Controls are hidden when there is only one page.

---

### `populateNodeFilter(statuses)`

Reads stage names from `statuses` (`Record<string, NodeStatus>`) to populate the filter dropdown, preserving the user's current selection when possible. Called by `main.ts` when `statusesChanged`.

## Event Listeners

- `searchInput` `input` event → Reset to page 1 and re-render
- `nodeFilter` `change` event → Reset to page 1 and re-render

## Error Record Fields

| Field | Description |
|-------|-------------|
| `error_id` | Error ID (integer) |
| `error_repr` | Error message string |
| `stage` | Stage tag |
| `task_repr` | Task content string |
| `ts` | Error timestamp (Unix seconds) |
