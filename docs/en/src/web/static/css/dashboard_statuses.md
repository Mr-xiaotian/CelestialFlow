# dashboard_statuses.css

> 📅 Last Updated: 2026/06/22

Responsible for the layout and style definitions of dashboard node status cards, including the stat grid, four-segment progress bar, and dynamic border colors based on node status.

## Layout Structure

### Stat Grid (`.stat-grid`)
- Uses `grid` layout, fixed at two columns.
- Used to display core metrics such as succeeded, pending, error, and duplicate.

### Node Card (`.node-card`)
- Adopts rounded card design (`border-radius: 1rem`).
- **Status Border**: A 3px-wide status bar on the left side, color dynamically changes based on node running status:
  - `.status-running`: Uses `--cornflower-400` (blue), indicating running.
  - `.status-stopped`: Uses `--carbon-400` (gray), indicating stopped.
  - Default: Uses `--carbon-300`, indicating not started.

## Progress Bar Rendering (`.progress-bar`)

The progress bar consists of four segments (`.progress-segment`), each corresponding to a different task status color:

| Class Name | Corresponding Metric | Light Mode Color | Dark Mode Color |
|------|----------|--------------|--------------|
| `.seg-success` | Succeeded | `--jade-400` | `--jade-700` |
| `.seg-error` | Error | `--crimson-400` | `--crimson-700` |
| `.seg-duplicate` | Duplicate | `--marigold-400` | `--marigold-700` |
| `.seg-pending` | Pending | `--carbon-300` | `--carbon-600` |

## Time Estimation Area (`.time-estimate`)

- Uses monospace font (`monospace`) to ensure alignment.
- The `.elapsed` series class names are used to color individual digits of the elapsed time (succeeded, error, duplicate).

## Interaction Effects

- **Click Feedback**:
  - `.error-clickable`: Error count items show a hand cursor (`pointer`), hinting that they are clickable for navigation.

## Responsive Design

- When width is less than `2048px`, `#dashboard-grid` switches to a single-column layout.
- Automatically handles long title wrapping logic.
