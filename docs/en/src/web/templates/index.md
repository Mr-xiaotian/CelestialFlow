# index.html

> 📅 Last Updated: 2026/05/15

The Jinja2 template file for the Web UI, defining the complete page structure of the monitoring system.

## Overall Layout

The page is divided into three main areas:

```
<header>  — Top control bar (settings panel, theme toggle)
<main>
  ├─ .tabs          — Tab navigation
  ├─ #dashboard     — Dashboard (three-column layout)
  ├─ #errors        — Error logs
  └─ #task-injection — Task injection
```

## Header Control Bar

| Element | ID / Class | Description |
|---------|-----------|-------------|
| Settings button | `#settings-btn` / `.btn-settings` | Gear SVG icon, click to open settings panel |
| Settings panel | `#settings-panel` / `.settings-panel` | Floating panel containing refresh interval and history length settings |
| Close button | `#settings-close` / `.settings-close` | Close button inside the settings panel |
| Refresh interval | `#refresh-interval` | Dropdown, options: 1s/2s/5s/10s/30s |
| History length | `#history-limit` | Dropdown, options: 10/20/50/100 |
| Theme toggle | `#theme-toggle` | Light/dark mode toggle button |

The settings panel is hidden by default (`hidden` class). Clicking the gear button toggles visibility; clicking outside the panel or the close button hides it.

## Tabs

| Tab ID | Button `data-tab` | Description |
|--------|-------------------|-------------|
| `#dashboard` | `dashboard` | Real-time task graph monitoring panel |
| `#errors` | `errors` | Error log list |
| `#task-injection` | `task-injection` | Task injection |

## Dashboard Three-Column Structure

### Left Column `.left-panel`

| Card | Class | Description |
|------|-------|-------------|
| Task Structure Diagram | `.mermaid-card` | Mermaid flowchart container `#mermaid-container` |
| Graph Analysis Info | `.analysis-card` | Displays DAG status, scheduling mode, layer count |

### Middle Column `.middle-panel`

| Card | Class | Description |
|------|-------|-------------|
| Node Running Status | `.status-card` | Dynamically generated node status card grid `#dashboard-grid` |

### Right Column `.right-panel`

| Card | Class | Description |
|------|-------|-------------|
| Node Completion Trend | `.progress-card` | Chart.js line chart `<canvas id="node-progress-chart">` |
| Overall Status Summary | `.summary-card` | 6-cell statistics: succeeded/pending/errors/duplicated/active nodes/remaining time |

> The actual column assignment and visibility of cards is dynamically controlled by `applyDashboardLayout()` in `web_config.ts`. All cards in the initial HTML are set to `display: none`.

## Error Log Panel

- Keyword search box `#error-search`
- Node filter dropdown `#node-filter`
- Error table `#errors-table` (columns: index / error id / error message / node / task / time)
- Pagination controls container `#pager-container`

## Task Injection Panel

- Node search `#search-input` + node list `#node-list`
- Select all / clear buttons
- Selected nodes area `#selected-section` / `#selected-list`
- Input method toggle: JSON text (`#json-textarea`) / file upload (`#file-input`)
- Insert termination signal shortcut button `fillTermination()`
- Submit button `#submit-btn` + status message `#status-message`

## External Dependencies (CDN)

| Library | Version | Purpose |
|---------|---------|---------|
| Chart.js | latest | Line charts |
| SortableJS | latest | Node card drag-and-drop sorting |
| Mermaid | `^10` (ESM) | Task graph visualization |

Mermaid is loaded via `<script type="module">` as an ESM module and mounted to `window.mermaid` for use by `task_structure.ts`.

## JS Script Loading Order

Scripts are loaded in the following order (dependency order):

```html
utils.js          ← Utility functions (no dependencies)
web_config.js     ← Depends on utils (references refreshSelect and other DOM elements)
task_statuses.js  ← Depends on utils
task_structure.js ← Depends on utils, task_statuses (reads nodeStatuses)
task_errors.js    ← Depends on utils, task_statuses (reads nodeStatuses)
task_analysis.js  ← Depends on utils
task_summary.js   ← Depends on utils
task_history.js   ← Depends on utils (extractProgressData, getColor)
task_injection.js ← Depends on task_statuses (reads nodeStatuses), utils
main.js           ← Depends on all above modules
```

## CSS Style References

```html
css/_colors.css    ← Color variable definitions
css/base.css       ← Global styles, theme variables, settings panel styles
css/dashboard.css  ← Dashboard, cards, progress bar styles
css/errors.css     ← Error table, pagination styles
css/inject.css     ← Task injection page styles
```
