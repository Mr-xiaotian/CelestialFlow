# errors.ts

> 📅 Last Updated: 2026/05/28

Manages error log paginated fetching, keyword search, node filtering, and table rendering.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `errors` | `any[]` | Current page's error record list |
| `currentPage` | `number` | Current page number displayed, starting from 1 |
| `pageSize` | `number` | Items per page, synced from `webConfig` |
| `totalPages` | `number` | Total pages calculated by the backend |
| `errorsRev` | `number` | Data version number, used for incremental fetch decisions |

## Functions

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword)`

Builds a cache key string for error queries, used to determine if filter conditions have changed and whether a forced refetch is needed.

- **Parameters**: Current page number, page size, node filter, search keyword
- **Return value**: A `|`-separated combined string, e.g., `"1|10|StageA|timeout"`
- Used together with `lastQueryKey` for query cache comparison

---

### `buildPageList(current, total)`

Generates a pagination page number list, including the first and last pages, the current page and its surrounding pages, automatically inserting ellipsis (`…`) at gaps.

- **Parameters**: `current` current page number, `total` total pages
- **Return value**: `Array<number | string>`, numeric page numbers or ellipsis strings
- Used internally by `renderPaginationControls()` to generate page number navigation

---

### `loadErrors(forceReload)`

Asynchronously fetches error log data. Supports incremental fetching based on `known_rev`.

- **Parameter**: `forceReload` (optional) - when `true`, forces ignoring cache and refetching (e.g., when search conditions change).
- **Query parameters**: `page`, `page_size`, `node` (node filter), `keyword` (fuzzy search).
- **Race condition protection**: Uses `errorsRequestSeq` to ensure old request results don't overwrite newer ones.

---

### `renderErrors()`

Renders `errors` data into the `#errors-table` table and calls `renderPaginationControls()` to update the pagination bar.

**Table Columns:**
1. Index (calculated from page number)
2. Error ID
3. Error Info (shows ellipsis for overflow, full text on hover)
4. Node (Node Tag)
5. Task (Task representation)
6. Time (Locally formatted time)

---

### `goToErrorsPage(nextPage)`

Pagination jump logic, triggers `loadErrors(true)` to refetch specific page data.

---

### `populateNodeFilter(statuses)`

Dynamically updates the "Filter by Node" dropdown on the error page based on dashboard node statuses.

---

### `renderPaginationControls(totalPages)`

Renders pagination controls, including previous/next buttons and numeric page sequence with ellipsis.

## Interactive Features

- **Search Linkage**: When the search box input or node filter changes, resets `currentPage` and forces a refresh.
- **Responsive Support**: On small-screen devices, the error table automatically switches to a card-style layout (via `errors.css` media queries).
- **External Navigation**: Supports one-click jumping from dashboard cards to the error log tab with auto-filled filter conditions via the global function `switchToErrorsTab(node?)` (defined in `utils.ts`).

## Usage Example

### Error Data Format and Processing

The following example shows the data structure of error logs and how to manually operate them in the browser console:

```typescript
// 1. Error record data structure (from backend)
const errorRecord = {
    ts: 1745400000,           // Timestamp (seconds)
    error_id: "err_001",     // Error ID
    error_repr: "Connection timeout after 30s",  // Error description
    error: {                  // Raw error object
        type: "TimeoutError",
        message: "Connection timeout after 30s",
        stack: "...",
    },
    stage: "DataLoader",     // Owning node
    task_repr: "file_123.json", // Task identifier
};

// 2. Simulate a batch of error data
const mockErrors = [
    { ts: 1745400100, error_id: "E001", error_repr: "Connection timeout", stage: "StageA", task_repr: "task_1", error: {} },
    { ts: 1745400050, error_id: "E002", error_repr: "Out of memory", stage: "StageB", task_repr: "task_5", error: {} },
    { ts: 1745400000, error_id: "E003", error_repr: "File not found", stage: "StageA", task_repr: "task_2", error: {} },
    { ts: 1745399950, error_id: "E004", error_repr: "Permission denied", stage: "StageC", task_repr: "task_3", error: {} },
];

// 3. Manually call error rendering
// Using global variables:
// errors = mockErrors;
// currentPage = 1;
// renderErrors();
// This renders the #errors-table with columns: index, error id, error info, node, task, time

// 4. Page navigation
// goToErrorsPage(2);  // Jump to page 2, triggers loadErrors(true)

// 5. Manually fetch errors using URL parameters
async function fetchErrorsManually(page: number, pageSize: number, node?: string, keyword?: string) {
    const params = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
    });
    if (node) params.set("node", node);
    if (keyword) params.set("keyword", keyword);

    const res = await fetch(`/api/pull_errors?${params}`);
    const data = await res.json();
    return data;
}

// Example: Get the first 5 errors for StageA
// fetchErrorsManually(1, 5, "StageA").then(data => console.log(data));

// 6. Render pagination controls
// renderPaginationControls(totalPages);
// Example: When totalPages is 5, generates: < 1 2 3 4 5 >

// 7. Jump from another tab to error log with auto-filter
// switchToErrorsTab("StageA");
// This will:
//   - Switch to the error log tab
//   - Set the node filter dropdown to "StageA"
//   - Trigger the query
```
