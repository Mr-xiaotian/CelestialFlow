# utils.ts

> 📅 Last Updated: 2026/05/15

A collection of shared utility functions used by all other frontend modules.

## Function List

### `renderLocalTime(timestamp)`

Converts a Unix timestamp (seconds) to a local time string.

```ts
renderLocalTime(1700000000) // → "2023/11/15 上午10:13:20" (varies by locale)
```

---

### `formatLargeNumber(n)`

Formats large numbers into approximate scientific notation HTML; numbers below 10 million are comma-separated, numbers at or above 10 million are converted to scientific notation.

```ts
formatLargeNumber(1234567890) // → "~1.23×10<sup>9</sup>"
formatLargeNumber(999)        // → "999"
```

---

### `formatWithDelta(value, delta, deltaClass, negClass)`

Formats a value and its delta, with the delta displayed as colored small text.

- `deltaClass`: CSS class name for positive deltas
- `negClass`: CSS class name for negative deltas

```ts
formatWithDelta(100, 5, "text-delta-success", "text-delta-success")
// → '100<small class="text-delta-success" style="margin-left: 4px;">+5</small>'
formatWithDelta(100, 0, ...)   // → '100'
```

Returns an HTML string for direct insertion into `innerHTML`.

---

### `getColor(index)`

Returns a predefined hex color from a set of 9 colors by cycling through the index, used for coloring line chart node lines.

```ts
getColor(0) // → "#3b82f6" (blue)
getColor(9) // → "#3b82f6" (cycles)
```

---

### `extractProgressData(nodeHistories)`

Extracts `{x, y}` point sequences from node history data for chart use.

- **Input**: `Record<string, NodeHistory>` — node name → history record array
- **Output**: `Record<string, Array<{x: number, y: number}>>` — node name → coordinate point array
  - `x`: Unix timestamp (seconds)
  - `y`: Tasks processed at that point in time

---

### `isMobile()`

Detects whether the current device is mobile (based on User-Agent). Returns `boolean`. Used to disable drag-and-drop sorting on mobile devices.

---

### `validateJSON(text)`

Validates whether a string is valid JSON.

- Empty strings are considered valid (returns `true`, hides error prompt)
- On parse failure, calls `showError("json-error", ...)` to display a prompt and returns `false`

---

### `escapeHtml(str)`

Escapes HTML special characters (`&`, `<`, `>`, `"`, `'`, `/`) to prevent XSS.

```ts
escapeHtml('<script>') // → "&lt;script&gt;"
```

---

### `toggleDarkTheme()`

Toggles the `dark-theme` CSS class on `document.body`. Returns whether dark mode is active after toggling (`boolean`).

---

### `switchToErrorsTab(nodeFilter?)`

Switches to the "Error Log" tab and optionally sets the node filter to the specified node. Passing no argument or an empty string shows all errors.

---

### `formatDuration(seconds)`

Formats seconds into an `HH:MM:SS` or `MM:SS` string.

```ts
formatDuration(90)    // → "01:30"
formatDuration(3661)  // → "01:01:01"
formatDuration(-5)    // → "00:00"
```

---

### `formatElapsedDuration(seconds, successCount, failedCount, duplicateCount)`

Formats elapsed time into a colored HTML string. Each digit character is wrapped in a `<span>`, with color classes assigned proportionally based on succeeded/failed/duplicated task ratios.

Internal call chain: `getElapsedSegments()` → `buildElapsedDigitClasses()` → `renderElapsedDurationHtml()`.

---

### `formatTimestamp(timestamp)`

Formats a Unix timestamp (seconds) into a `YYYY-MM-DD HH:MM:SS` string.

```ts
formatTimestamp(1700000000) // → "2023-11-15 10:13:20"
```
