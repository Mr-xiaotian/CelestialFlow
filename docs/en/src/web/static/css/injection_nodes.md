# injection_nodes.css

> 📅 Last Updated: 2026/06/22

Defines styles for the left-side node browse list of the task injection page, including node items, selected state, disabled state, and the "Edited" badge.

## Node List Container (`.node-list`)

- Vertical flex layout, `gap: 0.5rem`.
- `max-height: 30rem`, scrolls vertically when exceeded (`overflow-y: auto`).

## Node Item (`.node-item`)

- **Layout**: `flex` left-right distribution (node info + right-side badge), `gap: 0.75rem`.
- **Base style**: Rounded `0.75rem`, border `1px solid --carbon-200`.
- **Hover effect**: Background lightens (`--carbon-50`), border turns blue (`--cornflower-300`), slight upward shift `-1px`.
- **Dark mode**: Background `--carbon-700`, hover `--carbon-600`.

| CSS Class | Description |
|-----------|-------------|
| `.node-item` | Base node item style |
| `.node-item.active-node` | Currently selected node: blue border (`--cornflower-500`) + light blue background (`--cornflower-50`) |
| `.disabled-node` | Non-injectable node: `opacity: 0.55`, `cursor: not-allowed`, `pointer-events: none` |

## Node Info Area (`.node-info`)

- `min-width: 0`, `flex: 1`, allows text to shrink in narrow spaces.

## Node Name (`.node-name`)

- `font-weight: 600`, `word-break: break-all`.
- Light mode `--carbon-800`, dark mode `--carbon-100`.

## "Edited" Badge (`.node-side-tag`)

- `inline-flex`, `flex-shrink: 0`.
- Capsule shape (`border-radius: 999px`), small padding.
- Light mode: blue background (`--cornflower-100`) + blue text (`--cornflower-700`).
- Dark mode: dark blue background (`--cornflower-800`) + light blue text (`--cornflower-100`).

## Related Modules

- Node list is dynamically rendered by `renderNodeList()` in `injection.ts`.
- Selection logic is driven by `selectNode()`, with highlighting achieved by toggling the `.active-node` class.
- "Show injectable only" toggle filtering logic references `isInjectableNode()`.
