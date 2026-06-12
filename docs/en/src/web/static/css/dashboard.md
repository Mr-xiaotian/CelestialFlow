# dashboard.css

> 📅 Last Updated: 2026/05/23

Responsible for the dashboard page's core three-column layout architecture.

## Layout Architecture (`.three-column-container`)

The dashboard uses a widescreen three-column design, achieving structured page display through `flex` layout:

- **Left Panel (`.left-panel`)**: Takes 25%. Typically hosts the "Structure Diagram" and "Graph Analysis Info" cards.
- **Middle Panel (`.middle-panel`)**: Takes 40%. Core area, used to display the "Node Running Status" card grid.
- **Right Panel (`.right-panel`)**: Takes 25%. Displays the "Node Metric Trends (Line Chart)" and "Overall Status Summary" cards.

## Page Display Logic

- **Tab Switching**: Uses `.tab-content` and `.tab-content.active` with JS to enable instant switching between different function pages (Dashboard / Errors / Injection).

## Responsive Adaptation

- **Single Column Fallback**: When width is less than `2048px`, the layout automatically switches from horizontal three-column to vertical single-column flow layout, with all panels auto-expanding to `100%` width, ensuring readable metrics on small-screen devices.
