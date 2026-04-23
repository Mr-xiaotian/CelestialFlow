# web_config.ts

> 📅 Last updated: 2026/04/22

Manages web frontend configuration loading, saving, and application, including theme, refresh interval, and dashboard layout.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `webConfig` | `WebConfig \| null` | Current configuration object, loaded from the backend |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | CSS selector mapping for the three-column panels |

## Type Definitions

```ts
type WebConfig = {
    theme: "light" | "dark";
    refreshInterval: number;
    historyLimit: number;
    dashboard: {
        left: string[];
        middle: string[];
        right: string[];
    };
    cards: Record<string, { title: string }>;
};
```

## Functions

### `loadWebConfig()`

Asynchronously loads configuration from `GET /api/pull_config` and assigns it to `webConfig`.

- Returns `true` on success, `false` on failure
- Prints a warning to the console on failure without throwing an exception

---

### `saveWebConfig()`

Asynchronously POSTs the current `webConfig` to `/api/push_config` for backend persistence.

- Returns `true` on success, `false` on failure

---

### `applyConfig()`

Applies settings from `webConfig` to the UI:

1. **Theme**: Toggles the `dark-theme` CSS class and button text based on `webConfig.theme`
2. **Refresh Interval**: Updates `refreshRate` and the dropdown selected value (with boundary protection)
3. **Dashboard Layout**: Calls `applyDashboardLayout()`

---

### `applyDashboardLayout()`

Dynamically arranges dashboard cards based on `webConfig.dashboard` and `webConfig.cards` configuration.

**Flow:**

1. Collects all known card keys (from config + existing in DOM), locating the corresponding `.{key}-card` DOM elements
2. Hides all known cards first
3. In `left` / `middle` / `right` order, `appendChild` cards to the corresponding column, sets them visible, and updates titles
4. As a fallback, hides any cards not assigned to any column

> Movement is implemented via `appendChild`, supporting any column + any order configuration combinations.

## Configuration Structure

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "dashboard": {
        "left": ["mermaid", "topology"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    },
    "cards": {
        "mermaid": { "title": "Task Structure Diagram" },
        "topology": { "title": "Graph Topology Info" },
        "status": { "title": "Stage Runtime Status" },
        "progress": { "title": "Stage Completion Trend" },
        "summary": { "title": "Overall Status Summary" }
    }
}
```

Configuration is persisted on the backend in `web/config.json`; frontend changes are synced via `saveWebConfig()`.
