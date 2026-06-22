# dashboard_history.css

> 📅 Last Updated: 2026/06/22

Responsible for the control area styles above the node metric history chart (Chart.js), including the metric toggle button group.

## Layout Design (`.progress-card-header`)

- **Structure**: Uses `flex` layout, with card title on the left and metric switcher on the right.
- **Responsive**: Enables `flex-wrap: wrap`, auto-wraps on narrow screens.

## Metric Switcher (`.metric-indicators`)

- **Container**: `flex` layout, `flex-wrap: wrap`, centered, `gap: 1rem`.
- **Toggle Buttons (`.metric-dot`)**:
  - Each button contains a colored dot (`.dot`) and a text label (`.label`).
  - **Default state**: `opacity: 0.55`, de-emphasizes unselected metrics.
  - **Hover state**: `opacity: 0.8`.
  - **Active state (`.active`)**: `opacity: 1`, light gray background (`--carbon-100`), dark mode `--carbon-700`.
  - **Trend metrics (`.dot.delta`)**: Hollow circle (`background: transparent`, border-colored only), used to distinguish delta-type metrics from cumulative-type metrics.
- **Separator (`.metric-sep`)**: `1px` wide vertical line, used to separate cumulative metrics from trend metric groups.

## Related Modules

- The actual line chart is rendered by `dashboard_history.ts` with Chart.js in a canvas element; its internal colors (text, axis lines) are read from CSS variables in the TS code and set on the Chart.js instance.
- Metric switching is automatically bound by `initHistoryMetricSwitcher()` (module-level execution).
