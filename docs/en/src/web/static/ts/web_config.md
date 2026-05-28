# web_config.ts

> 📅 Last Updated: 2026/05/28

Manages web frontend configuration loading, normalization, saving, and application. Includes theme, language, polling frequency, history length, page size, and dashboard layout.

## Type Definitions

```ts
type WebConfig = {
    theme: "light" | "dark";         // UI theme
    refreshInterval: number;          // Global polling refresh interval (ms)
    historyLimit: number;             // History record length maintained locally by the frontend
    language: Lang;                   // UI language (zh-CN, en, ja)
    errorPageSize: number;            // Error log items per page
    showStructureEdgeDelta: boolean;  // Whether to show success task deltas on structure graph edges
    dashboard: {                      // Dashboard layout configuration
        left: string[];
        middle: string[];
        right: string[];
    };
};
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `webConfig` | `WebConfig \| null` | Current runtime configuration object |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | Default configuration template, used for initialization and fallback |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | Maps `left` / `middle` / `right` panel keys to CSS selectors (`.left-panel`, `.middle-panel`, `.right-panel`) |
| `CARD_TEMPLATES` | `Record<string, string>` | HTML template strings keyed by card ID (mermaid, analysis, status, progress, summary) |
| `CARD_META` | `Record<string, string>` | Maps card ID to its i18n label key (e.g. `mermaid` → `card.mermaid.title`) |
| `ALL_CARD_IDS` | `string[]` | Auto-generated from `Object.keys(CARD_TEMPLATES)`, used as the canonical card ID list for the layout editor |

## Functions

### `loadWebConfig()`

Asynchronously loads configuration from `GET /api/pull_config`.

- **Robustness**: If the request fails (e.g., backend not responding or network error), catches the exception and automatically calls `normalizeWebConfig()` to start with default configuration, ensuring the page remains basically functional.

---

### `saveWebConfig()`

POSTs the current `webConfig` object to `/api/push_config`. The backend persists it to `web/config.json`.

---

### `normalizeWebConfig(rawConfig?)`

Merges the raw configuration returned by the backend (which may have missing fields) with `DEFAULT_WEB_CONFIG`.

- Ensures the integrity of the `dashboard` structure.
- Provides deep merge logic.

---

### `applyConfig()`

Syncs settings from `webConfig` to the page:

1. **Language**: Applies `language` and updates all `data-i18n` elements on the page.
2. **Theme**: Toggles the `dark-theme` class.
3. **Parameter Sync**: Syncs refresh rate, history length, page size, and delta toggle to the corresponding DOM controls (e.g., Select/Checkbox).
4. **Layout**: Calls `applyDashboardLayout()` to rearrange cards.

---

### `ensureAllCards()`

Executes immediately at module load time. Iterates over `CARD_TEMPLATES` to create and inject all card DOM nodes into the `#card-pool` container.

- Checks for existing `.{key}-card` class elements to avoid duplicates
- Top-level module execution (not inside a function), ensuring subsequent scripts can find elements by ID before any layout operation

---

### `applyDashboardLayout()`

Core layout logic: Dynamically moves cards across the three-column panels via DOM operations (`appendChild`).

- **Dynamic Visibility**: Only cards present in the configuration are set to `display: block`.
- **Order Control**: Cards are inserted strictly following the order in the configuration array.

## Default Configuration Reference

```json
{
    "theme": "light",
    "refreshInterval": 5000,
    "historyLimit": 20,
    "language": "zh-CN",
    "errorPageSize": 50,
    "showStructureEdgeDelta": false,
    "dashboard": {
        "left": ["mermaid", "analysis"],
        "middle": ["status"],
        "right": ["progress", "summary"]
    }
}
```

## Usage Example

### Configuration Object Structure and Reading

The following example shows the complete structure of the `WebConfig` object and how to read and modify it in the browser console:

```typescript
// 1. Complete structure of WebConfig
// Referring to the default configuration, a complete config object contains:
const fullConfig: WebConfig = {
    theme: "light",
    refreshInterval: 5000,
    historyLimit: 20,
    language: "zh-CN",
    errorPageSize: 50,
    showStructureEdgeDelta: false,
    dashboard: {
        left: ["mermaid", "analysis"],
        middle: ["status"],
        right: ["progress", "summary"],
    },
};

// 2. Reading current configuration (in the browser console)
// The global variable webConfig holds the current runtime configuration
console.log("Current config:", webConfig);
console.log("Theme:", webConfig.theme);                   // "light" | "dark"
console.log("Refresh interval:", webConfig.refreshInterval, "ms"); // 5000
console.log("History limit:", webConfig.historyLimit);          // 20
console.log("Language:", webConfig.language);                // "zh-CN"
console.log("Error page size:", webConfig.errorPageSize);     // 50
console.log("Structure edge delta:", webConfig.showStructureEdgeDelta); // false
console.log("Dashboard layout:", webConfig.dashboard);
// { left: [...], middle: [...], right: [...] }

// 3. Using normalizeWebConfig to merge configurations
// When the backend returns a config that may be missing some fields, fill in with defaults:
const partialConfig = {
    theme: "dark",
    refreshInterval: 3000,
};
const normalized = normalizeWebConfig(partialConfig);
console.log("Normalized:", normalized);
// {
//   theme: "dark",
//   refreshInterval: 3000,
//   historyLimit: 20,           // default value
//   language: "zh-CN",          // default value
//   errorPageSize: 50,          // default value
//   showStructureEdgeDelta: false, // default value
//   dashboard: { left: [...], middle: [...], right: [...] } // default layout
// }

// 4. Manually modifying configuration and saving
async function updateConfig() {
    // Modify configuration
    webConfig.theme = "dark";
    webConfig.refreshInterval = 2000;
    webConfig.language = "en";

    // Apply configuration to the page
    applyConfig();

    // Save to backend
    const saved = await saveWebConfig();
    console.log(saved ? "Configuration saved successfully" : "Configuration save failed");
}

// 5. Dynamically adjusting dashboard layout
function rearrangeDashboard() {
    // Move status card to left column, structure diagram to middle column
    webConfig.dashboard = {
        left: ["status"],
        middle: ["mermaid"],
        right: ["analysis", "progress", "summary"],
    };
    applyDashboardLayout();
    saveWebConfig();
}

// 6. Using default configuration as fallback on startup
// When loadWebConfig() fails (e.g., backend not responding), fall back to default config:
// webConfig = normalizeWebConfig();
// This ensures the page renders properly under any circumstances
```
