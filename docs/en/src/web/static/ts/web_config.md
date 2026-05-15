# web_config.ts

> 📅 Last Updated: 2026/05/15

Manages web frontend configuration loading, saving, and application, including theme, refresh interval, history length, and dashboard layout.

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
3. **History Length**: Syncs `historyLimit` to the `#history-limit` dropdown (only sets the value when it exists among the available options, to avoid displaying a blank)
4. **Dashboard Layout**: Calls `applyDashboardLayout()`

---

### `applyDashboardLayout()`

Dynamically arranges dashboard cards based on `webConfig.dashboard` and `webConfig.cards` configuration.

**Flow:**

1. Collects all known card keys (from config + existing in DOM), locating the corresponding `.{key}-card` DOM elements
2. Hides all known cards first
3. In `left` / `middle` / `right` order, `appendChild` cards to the corresponding column and sets them visible
4. As a fallback, hides any cards not assigned to any column

> Movement is implemented via `appendChild`, supporting any column + any order configuration combinations.

## Configuration Structure

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "dashboard": {
        "left": ["mermaid", "analysis"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    },
    "cards": {
        "mermaid": { "title": "任务结构图" },
        "analysis": { "title": "图分析信息" },
        "status": { "title": "节点运行状态" },
        "progress": { "title": "节点完成走向" },
        "summary": { "title": "总体状态摘要" }
    }
}
```

Configuration is persisted on the backend in `web/config.json`; frontend changes are synced via `saveWebConfig()`.
