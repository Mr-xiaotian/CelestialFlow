# web_config.ts

> 📅 Last Updated: 2026/06/11

Manages web frontend configuration loading, normalization, saving, and application. Configuration uses a **grouped structure** (`global`, `dashboard`, `errors`, `injection`), while also supporting automatic migration of legacy flat format.

> ⚠️ **Changed**: The config structure has been refactored from the old flat `WebConfig` to a grouped format. Added `LegacyWebConfig` compatibility type, `isGroupedWebConfig()` detection function, and `normalizeDashboardLayout()` layout normalization function.

## Type Definitions

### Current Grouped Configuration

```typescript
type WebGlobalConfig = {
  theme: "light" | "dark";
  autoRefreshEnabled: boolean;
  refreshInterval: number;
  language: Lang;
};

type WebDashboardConfig = {
  historyLimit: number;
  showStructureEdgeDelta: boolean;
  useTotalPendingInStatus: boolean;
  layout: DashboardLayout;
};

type WebErrorsConfig = {
  pageSize: number;
  sortOrder: "newest" | "oldest";
  jumpToInjectionAfterRetry: boolean;
};

type WebInjectionConfig = {
  showInjectableOnly: boolean;
};

type WebConfig = {
  global: WebGlobalConfig;
  dashboard: WebDashboardConfig;
  errors: WebErrorsConfig;
  injection: WebInjectionConfig;
};
```

### Legacy Compatibility Type

```typescript
type LegacyWebConfig = {
  theme?: string;
  autoRefreshEnabled?: boolean;
  refreshInterval?: number;
  language?: string;
  historyLimit?: number;
  showStructureEdgeDelta?: boolean;
  useTotalPendingInStatus?: boolean;
  pageSize?: number;
  sortOrder?: string;
  jumpToInjectionAfterRetry?: boolean;
  showInjectableOnly?: boolean;
  layout?: DashboardLayout;
};
```

## Global Variables

| Variable | Type | Description |
|------|------|------|
| `webConfig` | `WebConfig` | Current runtime configuration object, initialized by `DEFAULT_WEB_CONFIG` at module load |
| `saveConfigPending` | `boolean` | Whether a save request is in progress (prevents concurrent writes) |
| `saveConfigPromise` | `Promise<boolean> \| null` | Promise of the current or most recent save operation |
| `PANEL_SELECTOR_MAP` | `Record<string, string>` | Panel key to CSS selector mapping |
| `CARD_TEMPLATES` | `Record<string, string>` | Card ID to HTML template mapping (mermaid, analysis, status, progress, summary) |
| `CARD_META` | `Record<string, string>` | Card ID to i18n label key mapping |
| `ALL_CARD_IDS` | `string[]` | Standard card ID list auto-generated from `Object.keys(CARD_TEMPLATES)` |
| `DEFAULT_WEB_CONFIG` | `WebConfig` | Default configuration template, used for initialization and fallback |

## Functions

### `loadWebConfig(): Promise<void>`

Asynchronously loads configuration from `GET /api/pull_config`. Automatically falls back to default configuration on failure.

---

### `saveWebConfig(): Promise<boolean>`

Persists the current `webConfig` via `POST /api/push_config`. Has **anti-concurrency** mechanism: if a save is already in progress, reuses the same Promise.

---

### `performSaveWebConfig(): Promise<boolean>`

Executes the actual POST request. Sets the `saveConfigPending` flag and returns the write result.

---

### `isGroupedWebConfig(config: unknown): boolean`

Detects whether a config object is the new grouped format (contains `global`, `dashboard`, `errors`, `injection` sub-objects).

---

### `normalizeWebConfig(rawConfig?: unknown): WebConfig`

Deep-merges the raw config returned by the backend (potentially legacy flat format or with missing fields) with `DEFAULT_WEB_CONFIG`.

- Auto-detects and migrates legacy flat config (`LegacyWebConfig`) to the new grouped format.
- Ensures `dashboard.layout` integrity.

---

### `normalizeDashboardLayout(layout?: Partial<DashboardLayout>): DashboardLayout`

Ensures the dashboard layout contains all three column keys (`left`, `middle`, `right`), filling with empty arrays when missing.

---

### `applyConfig(): void`

Syncs various settings from `webConfig` to the page:

1. **Language**: Applies `global.language` and updates all `data-i18n` elements on the page.
2. **Theme**: Toggles the `dark-theme` class based on `global.theme`.
3. **Parameter Sync**: Syncs refresh rate, history limit, page size, delta toggles, etc. to the corresponding DOM controls.
4. **Layout**: Calls `applyDashboardLayout()` to rearrange cards.

---

### `ensureAllCards(): void`

Executed immediately at module load, iterates `CARD_TEMPLATES` to create all card DOM nodes and inject them into the `#card-pool` container. Checks whether elements with corresponding class names already exist to avoid duplicate creation.

---

### `applyDashboardLayout(): void`

Core layout logic: implements dynamic movement of cards between three column panels via DOM manipulation (`appendChild`). Strictly follows the order in the config arrays.

## Default Configuration Reference

```typescript
const DEFAULT_WEB_CONFIG: WebConfig = {
  global: {
    theme: "light",
    autoRefreshEnabled: true,
    refreshInterval: 5000,
    language: "zh-CN",
  },
  dashboard: {
    historyLimit: 20,
    showStructureEdgeDelta: false,
    useTotalPendingInStatus: false,
    layout: {
      left: ["mermaid", "analysis"],
      middle: ["status"],
      right: ["progress", "summary"],
    },
  },
  errors: {
    pageSize: 50,
    sortOrder: "newest",
    jumpToInjectionAfterRetry: true,
  },
  injection: {
    showInjectableOnly: false,
  },
};
```

## Usage Example

```typescript
// Read current configuration
console.log("Theme:", webConfig.global.theme);
console.log("Refresh Interval:", webConfig.global.refreshInterval);
console.log("History Limit:", webConfig.dashboard.historyLimit);
console.log("Errors Per Page:", webConfig.errors.pageSize);
console.log("Injection Injectable Only:", webConfig.injection.showInjectableOnly);

// Modify configuration and save
webConfig.global.theme = "dark";
webConfig.dashboard.historyLimit = 50;
applyConfig();  // Immediately apply to page
const saved = await saveWebConfig();  // Persist to backend

// Legacy flat config auto-migration
const legacy = { theme: "dark", refreshInterval: 3000, historyLimit: 10 };
const normalized = normalizeWebConfig(legacy);
// Auto-migrated to { global: { theme: "dark", ... }, dashboard: { historyLimit: 10, ... }, ... }
```
