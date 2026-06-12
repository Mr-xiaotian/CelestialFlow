# dashboard_analysis.css

> 📅 Last Updated: 2026/05/23

Responsible for the style definitions of the "Graph Analysis Info" card in the bottom-left of the dashboard.

## Layout Design (`.analysis-info`)

- **Structure**: Uses vertical `flex` layout to display a key-value pair list.
- **Font**: Uses small font size (`0.75rem`) to accommodate more metadata information.

## Data Row Style (`.analysis-row`)

- **Left-Right Alignment**: Label name (Label) on the left, specific value (Value) on the right.
- **Status Colors (`.analysis-value`)**:
  - `.ok`: Green (`--jade-600`), indicating expected behavior (e.g., is a DAG).
  - `.warn`: Red (`--crimson-600`), indicating potential risk (e.g., cycles exist).

## Related Modules

- Data rendering is handled by `dashboard_analysis.ts`, which dynamically assigns `ok` or `warn` classes based on the analysis results returned by the backend (e.g., whether it is a DAG).
