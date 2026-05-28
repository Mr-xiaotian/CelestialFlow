# index.html

> 📅 Last Updated: 2026/05/28

The Jinja2 template file for the Web UI, defining the complete page structure of the monitoring system.

## Overall Layout

The page is divided into three main areas:

```
<header>  — Top control bar (settings panel, theme toggle)
<main>
  ├─ .tabs           — Tab navigation (Dashboard / Error Logs / Task Injection)
  ├─ #dashboard      — Dashboard (three-column layout)
  ├─ #errors         — Error logs
  └─ #task-injection  — Task injection
```

## Header Control Bar

| Element | ID / Class | Description |
|---------|-----------|-------------|
| Settings button | `#settings-btn` | Click to open settings panel, with a11y attributes |
| Settings panel | `#settings-panel` | Contains refresh, history, language, page size, delta toggle and other settings |
| UI Language | `#language-select` | Supports Chinese, English, and Japanese switching |
| Structure Edge Delta | `#structure-edge-delta` | Toggle controlling whether success count deltas are shown on Mermaid graph edges |
| Theme toggle | `#theme-toggle` | Rounded capsule button, switches between light and dark modes |

## Dashboard Three-Column Structure

### Left Column `.left-panel`

| Card | Class | Description |
|------|-------|-------------|
| Task Structure Diagram | `.mermaid-card` | Mermaid flowchart, supports node coloring and edge deltas |
| Graph Analysis Info | `.analysis-card` | Topological structure insight information |

### Middle Column `.middle-panel`

| Card | Class | Description |
|------|-------|-------------|
| Node Running Status | `.status-card` | Dynamic node cards with progress bars and real-time delta statistics |

### Right Column `.right-panel`

| Card | Class | Description |
|------|-------|-------------|
| Node Metric Trend | `.progress-card` | History line chart supporting metric switching (processed/succeeded/failed/duplicated/pending) |
| Overall Status Summary | `.summary-card` | Global 6-cell statistics dashboard |

## External Dependencies (CDN)

| Library | Version | Purpose |
|---------|---------|---------|
| Chart.js | latest | Line chart rendering |
| SortableJS | latest | Node card drag-and-drop sorting |
| Mermaid | `^10` (ESM) | Task graph visualization rendering |

## JS Script Loading Order

Scripts are loaded in dependency order:

```html
i18n.js               ← Internationalization support
utils.js              ← Common utility functions
web_config.js         ← Configuration management logic
dashboard_statuses.js ← Node status management
dashboard_structure.js← Structure diagram rendering
errors.js             ← Error log pagination
dashboard_analysis.js ← Topology analysis display
dashboard_summary.js  ← Summary statistics
dashboard_history.js  ← History chart
injection.js          ← Task injection logic
layout_editor.js      ← Card layout editor (depends on web_config's CARD_TEMPLATES, PANEL_SELECTOR_MAP, and applyDashboardLayout)
main.js               ← Global entry point and polling coordination
```

## CSS Style References

```html
css/_colors.css             ← Color variable definitions
css/base.css                ← Global base styles and settings panel
css/dashboard.css           ← Dashboard layout and tab container
css/dashboard_structure.css  ← Structure diagram specific styles
css/dashboard_analysis.css   ← Analysis card specific styles
css/dashboard_statuses.css   ← Node card specific styles
css/dashboard_summary.css    ← Summary panel specific styles
css/dashboard_history.css    ← History chart specific styles
css/errors.css              ← Error log page styles
css/injection.css           ← Task injection page styles
```

## Card Layout Editor Modal (`#layout-editor-overlay`)

Floating modal window (hidden by default via `.overlay.hidden`) supporting drag-and-drop reordering of the three-column dashboard cards.

- **Overlay**: `#layout-editor-overlay` / `.overlay` — full-screen semi-transparent black background, `z-index: 200`
- **Editor Body**: `#layout-editor` / `.layout-editor` — rounded card container, `max-width: 700px`
- **Three-Column Drop Zones**: Left, middle, right drop zones (`#layout-dropzone-left`, `#layout-dropzone-middle`, `#layout-dropzone-right`), drag-and-drop based on SortableJS
- **Unused Pool**: `#layout-dropzone-unused` — horizontal drop zone for cards removed from the three columns
- **Footer Buttons**: Save (`#layout-save-btn`) and reset to default (`#layout-reset-btn`)
- Opened via the `.btn-layout-editor` button in the settings panel; closed by clicking `#layout-editor-close` or outside the overlay
- On save, calls `applyDashboardLayout()` for immediate effect, then `saveWebConfig()` to persist to the backend

## Usage Example

### Accessing via Browser

After starting the web server, access in the browser address bar:

```
http://127.0.0.1:5000
```

Startup command:

```bash
# Command line startup (default 0.0.0.0:5000)
celestialflow-web

# Or start in Python
python -c "from celestialflow import TaskWebServer; TaskWebServer(host='127.0.0.1', port=5000).start_server()"
```

After opening in the browser, three tabs are visible:
- **Dashboard**: Real-time display of task graph structure diagram, node running status, metric trends, and overall summary
- **Error Logs**: Paginated viewing and searching of error records
- **Task Injection**: Inject new tasks into specified nodes

### Modifying the Template

`index.html` uses the Jinja2 template engine. You can customize the interface through custom template variables or by directly modifying the HTML.

#### Changing the Page Title

Edit `index.html` and find the `<title>` tag:

```html
<!-- Original -->
<title>Task Graph Monitoring System</title>

<!-- Changed to custom title -->
<title>My Task Monitor</title>
```

#### Adjusting Dashboard Layout

The template hardcodes the three-column structure (left-panel / middle-panel / right-panel). You can swap positions by modifying the corresponding card container order:

```html
<!-- Swap structure diagram and analysis info -->
<div class="left-panel">
  <div class="analysis-card"><!-- Analysis panel --></div>
  <div class="mermaid-card"><!-- Structure diagram --></div>
</div>
```

#### Dynamic Control via Configuration

The runtime card layout is actually controlled by `WebConfig.dashboard`. Modify defaults in `web_config.ts` or adjust via backend `config.json`:

```json
{
    "dashboard": {
        "left": ["status"],
        "middle": ["mermaid"],
        "right": ["summary", "progress"]
    }
}
```

#### Adding Custom CSS

Place custom style files in the `web/static/css/` directory and reference them in `index.html`:

```html
<link rel="stylesheet" href="static/css/custom.css">
```
