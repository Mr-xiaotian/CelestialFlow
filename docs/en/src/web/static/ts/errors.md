# errors.ts

> 📅 Last Updated: 2026/06/11

Manages paginated fetching of error logs, keyword search, node filtering, sort order switching, table rendering, and task re-injection functionality.

> ⚠️ **Changed**: Error record fields have been restructured (`error_id` is now numeric, new `error_type`/`error_message` fields, `task` is `unknown`). Added sort toggle and retry (re-injection) interaction column.

## Type Definitions

```typescript
type ErrorData = {
  ts: number;            // Error occurrence timestamp, in seconds
  stage: string;         // Node/stage name where the error occurred, used for node filtering
  error_id: number;      // Globally unique error identifier
  error_type: string;    // Error classification type, used to distinguish different error categories
  error_message: string; // Specific error description
  task: unknown;         // Task data that triggered this error, used for display and retry backfill
};
```

## Global Variables

| Variable | Type | Description |
|------|------|------|
| `errors` | `ErrorData[]` | Error record list for the current page |
| `currentPage` | `number` | Currently displayed page number, starting from 1 |
| `pageSize` | `number` | Records per page, synced from `webConfig` |
| `errorSortOrder` | `"newest" \| "oldest"` | Error log sort direction, default `"newest"` |
| `totalPages` | `number` | Total pages calculated by the backend |
| `errorsRev` | `number` | Data revision number, initialized to `-1`, used for incremental fetch |
| `lastQueryKey` | `string` | Cached key of the last query, used to determine if filter conditions changed |
| `errorsRequestSeq` | `number` | Request sequence number, prevents old requests from overwriting new results |

## DOM Element References

| Variable | DOM Selector | Description |
|------|-----------|------|
| `searchInput` | `#error-search` | Search keyword input |
| `nodeFilter` | `#node-filter` | Node filter dropdown |
| `errorSortSelect` | `#error-sort-order` | Sort order dropdown |
| `errorsTableBody` | `#errors-table tbody` | Error table tbody |
| `paginationContainer` | `#pager-container` | Pagination controls container |

## Functions

### `buildErrorsQueryKey(page, pageSizeValue, node, keyword, sortOrder): string`

Builds a cache key string for error queries. Parameters include `sortOrder` (newest/oldest), used with `lastQueryKey` to determine if filter conditions changed.

---

### `loadErrors(forceReload?: boolean): Promise<boolean>`

Asynchronously fetches error log data.

- **Query params**: `known_rev`, `page`, `page_size`, `node`, `keyword`, `sort_order`
- **Race protection**: Uses `errorsRequestSeq` to ensure old request results don't overwrite new ones.
- **Force reload**: When `forceReload=true` or filter conditions change, ignores `known_rev` incremental mechanism.
- **API endpoint**: `GET /api/pull_errors?{params}`

---

### `renderErrors(): void`

Renders `errors` data into the `#errors-table` table.

**Table columns (7 total):**

| # | Column Name (i18n key) | Description |
|---|----------------|------|
| 1 | `#` | Global display index (computed from page number) |
| 2 | `errors.colId` | Error ID |
| 3 | `errors.colMessage` | Error message (truncated `format_repr` to 50 chars, full on hover) |
| 4 | `errors.colNode` | Node name |
| 5 | `errors.colTask` | Task data (truncated display) |
| 6 | `errors.colTime` | Occurrence time (`formatTimestamp` formatted) |
| 7 | `errors.colRetry` | Re-injection action: `.retry-link` (retryable) or `.retry-disabled` (unavailable) |

> Column 7 (Re-injection): When `task` exists and is not a placeholder, click/keyboard triggers `preloadInjectionDraftFromError(stage, task, jumpToInjectionAfterRetry)`, navigating to the injection page pre-filled with task data.

---

### `goToErrorsPage(nextPage: number): Promise<void>`

Pagination navigation logic, clamps page number to `[1, totalPages]` range then triggers `loadErrors(true)` to re-fetch.

---

### `buildPageList(current: number, total: number): Array<number | string>`

Generates a pagination page number list, including first/last pages, current page, and ±2 adjacent pages, auto-inserting ellipsis `"…"`.

---

### `renderPaginationControls(totalPages: number): void`

Renders pagination controls (prev/next buttons + numeric page sequence). Not rendered when `totalPages ≤ 1`.

---

### `populateNodeFilter(statuses: Record<string, NodeStatus>): void`

Dynamically updates the error page's "filter by node" dropdown based on dashboard node statuses. Attempts to preserve the user's current filter selection.

---

## Event Bindings (Module-level Auto-execution)

| Target Element | Event | Behavior |
|----------|------|------|
| `searchInput` | `input` | Reset to page 1, force reload, render table |
| `nodeFilter` | `change` | Reset to page 1, force reload, render table |
| `errorSortSelect` | `change` | Update `errorSortOrder` and `webConfig`, reset to page 1, reload and save config |

## Usage Example

```typescript
// Simulated error records
const mockErrors: ErrorData[] = [
  { ts: 1745400100, stage: "StageA", error_id: 1001, error_type: "TimeoutError", error_message: "Connection timeout", task: { id: 1 } },
  { ts: 1745400050, stage: "StageB", error_id: 1002, error_type: "ValueError", error_message: "Invalid value", task: "task_data" },
];

// errors = mockErrors;
// currentPage = 1;
// totalPages = 5;
// renderErrors();        // Render table
// renderPaginationControls(5); // Render pagination

// Navigate to page 3
// await goToErrorsPage(3);

// Jump to error log from another tab with auto-filter
// switchToErrorsTab("StageA");
```

## Data Flow

```mermaid
flowchart LR
    subgraph "main.ts"
        RA[refreshAll]
    end
    subgraph "errors.ts"
        LE[loadErrors]
        QK[buildErrorsQueryKey]
        RE[renderErrors]
        RP[renderPaginationControls]
    end
    subgraph "API"
        API[/api/pull_errors]
    end
    subgraph "DOM"
        TB[#errors-table]
        PG[#pager-container]
    end

    RA --> LE
    LE --> QK
    LE --> API
    API --> LE
    LE --> RE
    RE --> TB
    RE --> RP
    RP --> PG
```
