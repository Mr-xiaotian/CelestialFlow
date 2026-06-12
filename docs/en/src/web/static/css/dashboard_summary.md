# dashboard_summary.css

> 📅 Last Updated: 2026/05/23

Responsible for the style definitions of the "Overall Status Summary" panel in the bottom-right of the dashboard, using vividly colored stat cards to display global runtime metrics.

## Layout Structure (`.summary-grid`)

- Uses `grid` layout, fixed at two columns.
- Each grid cell contains a `.summary-item`.

## Stat Cards (`.summary-item`)

Each stat item is assigned a different theme color based on its semantics, including background color (`.summary-item`) and value text color (`.summary-value`):

| Stat Item | Class Name | Primary Tone | Semantic |
|--------|------|--------|------|
| **Total Succeeded** | `.success` | `Jade` (green) | Tasks completed successfully |
| **Total Pending** | `.pending` | `Carbon` (gray) | Queued, awaiting processing |
| **Total Error** | `.error` | `Crimson` (red) | Processing failed, needs attention |
| **Total Duplicate** | `.duplicate` | `Marigold` (orange) | Hit dedup logic |
| **Active Nodes** | `.nodes` | `Cornflower` (blue) | Number of currently running stages |
| **Total Remaining Time** | `.remain` | `Violet` (purple) | Global progress estimate |

## Style Characteristics

- **Visual hierarchy**: Values use `2rem` bold font, labels use `0.75rem` gray small text.
- **Dark mode**: Automatically switches background colors to dark tones (e.g., `900` series) and text colors to light tones (e.g., `300` series), ensuring contrast.
- **Interaction cues**:
  - When total error count is greater than 0, `.summary-value.error-clickable` displays a hand cursor, guiding the user to click and navigate to view error details.
