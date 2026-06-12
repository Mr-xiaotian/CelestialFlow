# errors.css

> 📅 Last Updated: 2026/05/23

Responsible for the style definitions of the search box, filters, data table, and pagination controls under the "Error Log" tab.

## Search & Filter (`.filter-container`)

- **Layout**: Uses `flex` layout, with title on the left and search input and node filter dropdown on the right.
- **Search Box (`.error-search-input`)**:
  - Has smooth transition effects (`transition: all 0.2s`).
  - **Focus state**: On focus, border color deepens and background color slightly changes for visual feedback.

## Data Table (`#errors-table`)

- **Structure**: Standard HTML table, but automatically converts to a card flow layout on mobile/narrow screens.
- **Cell Styles**:
  - `.error-id`: Uses gray tones for IDs, reducing visual noise.
  - `.error-cell`: Specifically for displaying error repr, using monospace font (`monospace`) and red tones (`Crimson`). To prevent overly long error messages from breaking the layout, sets `max-width: 40ch` and truncates with ellipsis (`ellipsis`).

## Pagination Controls (`.pager-container`)

- **Page Links (`.pager-link`)**: Supports hover highlighting.
- **Navigation Buttons (`.pager-btn`)**:
  - Contains "Previous" and "Next" icon buttons.
  - **Disabled state**: When on the first or last page, buttons become gray and unclickable (`cursor: not-allowed`).

## Responsive Design

- **Table-to-Card**: When width is less than `2048px`, the table `thead` is hidden and each row `tr` becomes an independent card block with rounded borders.
- **Pseudo-element Labels**: Injects table column names inside the card via `::before { content: attr(data-label) }`, allowing mobile users to still identify data meanings.
- **Error Expansion**: In card mode, `.error-cell`'s truncation limit is removed (`white-space: normal`), switching to auto-wrapping to show more detail.
