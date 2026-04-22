# index.html

> 📅 Last updated: 2026/04/22

The Jinja2 template file for the Web UI, defining the complete page structure of the monitoring system.

## Overall Layout

The page is divided into three main areas:

```
<header>  — Top control bar (refresh interval, theme toggle)
<main>
  ├─ .tabs          — Tab navigation
  ├─ #dashboard     — Dashboard (three-column layout)
  ├─ #errors        — Error logs
  └─ #task-injection — Task injection
```

## Tabs

| Tab ID | Button `data-tab` | Description |
|--------|-------------------|-------------|
| `#dashboard` | `dashboard` | Real-time task graph monitoring panel |
| `#errors` | `errors` | Error log list |
| `#task-injection` | `task-injection` | Task injection |

## Dashboard Three-Column Structure

### Left Column `.left-panel`

| Card | ID / Class | Default Display | Description |
|------|-----------|-----------------|-------------|
| Task Structure Diagram | `.mermaid-card` | Determined by layout config | Mermaid flowchart container `#mermaid-container` |
| Graph Topology Info | `.topology-card` / `#topology-card` | Determined by layout config | Displays DAG status, scheduling mode, layer count |

### Middle Column `.middle-panel`

| Card | Class | Description |
|------|-------|-------------|
| Stage Runtime Status | `.status-card` | Dynamically generated stage status card grid `#dashboard-grid` |

### Right Column `.right-panel`

| Card | Class | Description |
|------|-------|-------------|
| Stage Completion Trend | `.progress-card` | Chart.js line chart `<canvas id="node-progress-chart">` |
| Overall Status Summary | `.summary-card` | 6-cell statistics: success/pending/errors/duplicates/active nodes/remaining time |

> The actual column assignment and visibility of cards is dynamically controlled by `applyDashboardLayout()` in `web_config.ts`. All cards in the initial HTML are set to `display: none`.

## Error Log Panel

- Keyword search box `#error-search`
- Stage filter dropdown `#node-filter`
- Error table `#errors-table` (columns: error ID / error message / stage / task / time)
- Pagination controls container `#pagination-container`

## Task Injection Panel

- Stage search `#search-input` + stage list `#node-list`
- Select all / clear buttons
- Selected stages area `#selected-section` / `#selected-list`
- Input method toggle: JSON text (`#json-textarea`) / file upload (`#file-input`)
- Insert termination signal shortcut button `fillTermination()`
- Submit button `#submit-btn` + status message `#status-message`

## External Dependencies (CDN)

| Library | Version | Purpose |
|---------|---------|---------|
| Chart.js | latest | Line charts |
| SortableJS | latest | Drag-and-drop sorting for stage cards |
| Mermaid | `^10` (ESM) | Task graph visualization |

Mermaid is loaded via `<script type="module">` as an ESM module and mounted to `window.mermaid` for use by `task_structure.ts`.

## JS Script Loading Order

Scripts are loaded in the following order (dependency order):

```html
utils.js          ← Utility functions (no dependencies)
task_statuses.js  ← Depends on utils
task_structure.js ← Depends on utils, task_statuses (reads nodeStatuses)
task_errors.js    ← Depends on utils, task_statuses (reads nodeStatuses)
task_topology.js  ← Depends on utils
task_summary.js   ← Depends on utils
task_history.js   ← Depends on utils (extractProgressData, getColor)
task_injection.js ← Depends on task_statuses (reads nodeStatuses), utils
main.js           ← Depends on all above modules
```

## CSS Style References

```html
css/base.css       ← Global styles, theme variables
css/dashboard.css  ← Dashboard, cards, progress bar styles
css/errors.css     ← Error table, pagination styles
css/inject.css     ← Task injection page styles
```
