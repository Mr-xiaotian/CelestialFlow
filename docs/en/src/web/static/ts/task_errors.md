# task_errors.ts

> 📅 Last Updated: 2026/05/15

Manages error log data loading, server-side pagination/filtering, and rendering.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `errors` | `any[]` | Current page's error record array, fetched from backend |
| `currentPage` | `number` | Current page number, default 1 |
| `pageSize` | `number` | Items per page, fixed at 10 |
| `totalPages` | `number` | Total pages, returned from backend |
| `errorsRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |
| `lastQueryKey` | `string` | Last query cache key, used to detect filter condition changes |
| `errorsRequestSeq` | `number` | Request sequence number, prevents stale requests from overwriting newer results |

## DOM Element References

| Variable | Selector | Description |
|----------|----------|-------------|
| `searchInput` | `#error-search` | Keyword search input |
| `nodeFilter` | `#node-filter` | Node filter dropdown |
| `errorsTableBody` | `#errors-table tbody` | Error table body |
| `paginationContainer` | `#pager-container` | Pagination controls container |

## Functions

### `buildErrorsQueryKey(page, pageSize, node, keyword)`

Combines pagination and filter parameters into a cache key string (`page|pageSize|node|keyword`), used to detect whether query conditions have changed.

---

### `loadErrors(forceReload?)`

Asynchronously fetches error data from `GET /api/pull_errors`, supporting server-side pagination and filtering.

**Request Parameters:**

| Parameter | Description |
|-----------|-------------|
| `known_rev` | Version number; reset to -1 when filter conditions change or `forceReload` is set |
| `page` | Current page number |
| `page_size` | Items per page |
| `node` | Node filter value |
| `keyword` | Search keyword |

**Race condition protection:** Uses an incrementing `errorsRequestSeq` sequence number; when a response arrives, the sequence number is verified to match, and stale responses are discarded.

---

### `renderErrors()`

Renders the error table. Columns: index, error id, error message, node, task, time. Displays a placeholder message when there is no data.

---

### `goToErrorsPage(nextPage)`

Navigates to the specified page, calling `loadErrors(true)` to force reload and re-render.

---

### `buildPageList(current, total)`

Generates a smart page number array containing the first and last pages, the current page and its surrounding 2 pages, with gaps filled by `"..."`.

---

### `renderPaginationControls(totalPages)`

Renders pagination controls, including "Previous"/"Next" buttons and numeric page buttons. Controls are hidden when there is only one page.

---

### `populateNodeFilter(statuses)`

Reads node names from `statuses` (`Record<string, NodeStatus>`) to populate the filter dropdown, preserving the user's current selection when possible. Called by `main.ts` when `statusesChanged`.

## Event Listeners

- `searchInput` `input` event → Reset to page 1, force reload and re-render
- `nodeFilter` `change` event → Reset to page 1, force reload and re-render

## Error Record Fields

| Field | Description |
|-------|-------------|
| `error_id` | Error ID (integer) |
| `error_repr` | Error message string |
| `stage` | Owning node tag |
| `task_repr` | Task content string |
| `ts` | Error timestamp (Unix seconds) |
