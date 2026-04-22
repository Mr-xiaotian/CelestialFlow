# utils.ts

A collection of general-purpose utility functions shared by all other frontend modules.

## Function List

### `renderLocalTime(timestamp)`

Converts a Unix timestamp (seconds) to a local time string.

```ts
renderLocalTime(1700000000) // → "2023/11/15 上午10:13:20" (depends on locale)
```

---

### `formatLargeNumber(n)`

Formats large numbers into approximate scientific notation HTML; numbers less than 10000 are returned as plain strings.

```ts
formatLargeNumber(1234567890) // → "~1.23×10<sup>9</sup>"
formatLargeNumber(999)        // → "999"
```

---

### `formatWithDelta(value, delta, deltaClass, negClass)`

Formats a value with its delta; the delta is displayed as colored small text.

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

Returns a predefined hex color from a palette of 9 colors by cycling through the index. Used for coloring line chart traces.

```ts
getColor(0) // → "#3b82f6" (blue)
getColor(9) // → "#3b82f6" (cycles)
```

---

### `extractProgressData(nodeHistories)`

Extracts `{x, y}` point sequences from node history data for chart rendering.

- **Input**: `Record<string, NodeHistory>` -- node name → history record array
- **Output**: `Record<string, Array<{x: number, y: number}>>` -- node name → coordinate point array
  - `x`: Unix timestamp (seconds)
  - `y`: Number of tasks processed at that point

---

### `isMobile()`

Detects whether the current device is mobile (based on User-Agent). Returns `boolean`. Used to disable drag-and-drop sorting on mobile devices.

---

### `validateJSON(text)`

Validates whether a string is valid JSON.

- Empty strings are considered valid (returns `true`, hides error message)
- On parse failure, calls `showError("json-error", ...)` to display a message, returns `false`

---

### `escapeHtml(str)`

Escapes HTML special characters (`&`, `<`, `>`, `"`), preventing XSS.

```ts
escapeHtml('<script>') // → "&lt;script&gt;"
```

---

### `toggleDarkTheme()`

Toggles the `dark-theme` CSS class on `document.body`. Returns whether dark mode is active after toggling (`boolean`).

---

### `switchToErrorsTab(nodeFilter?)`

Switches to the "Error Logs" tab, optionally setting the stage filter to the specified stage. Passing no argument or an empty string shows all errors.

---

### `formatDuration(seconds)`

Formats seconds into an `HH:MM:SS` or `MM:SS` string.

```ts
formatDuration(90)    // → "01:30"
formatDuration(3661)  // → "01:01:01"
formatDuration(-5)    // → "00:00"
```

---

### `formatTimestamp(timestamp)`

Formats a Unix timestamp (seconds) into a `YYYY-MM-DD HH:MM:SS` string.

```ts
formatTimestamp(1700000000) // → "2023-11-15 10:13:20"
```
