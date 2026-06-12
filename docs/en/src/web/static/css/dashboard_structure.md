# dashboard_structure.css

> 📅 Last Updated: 2026/05/23

Responsible for the container layout and theme adaptation of the task structure diagram (Mermaid.js rendered content).

## Container Layout (`#mermaid-container`)

- **Alignment**: Uses `flex` layout for horizontal and vertical centering of content.
- **Scroll Support**: Enables `overflow-x: auto`, ensuring users can horizontally scroll to view the full topology in large, complex graph structures.

## Mermaid Theme Adaptation

Since the SVG internal styles rendered by Mermaid are difficult to override via regular CSS, this file primarily enforces key style overrides for dark mode (`.dark-theme`):

- **Arrow Color (`.arrowMarkerPath`)**: In dark mode, sets the arrow fill color to `--carbon-200`, enhancing edge visibility.
- **Node Text (`span`)**: Forcefully overrides internal node text color to `--carbon-300`, ensuring readability against dark background nodes.

## Related Modules

- Specific node background colors, border colors, and edge styles (`classDef`) are defined in the dynamically generated Mermaid code within `dashboard_structure.ts` based on the current theme, not in this CSS file.
