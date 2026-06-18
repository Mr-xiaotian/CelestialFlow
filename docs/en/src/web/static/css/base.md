# base.css

> 📅 Last Updated: 2026/06/18

Responsible for the system's global base styles, dark mode switching, common components (cards, tabs, badges), responsive base layout, and card layout editor modal window styles.

## Global Base

- **Reset**: Unified box model (`border-box`) and default font family.
- **Background & Color**: Defines body background color in light (`--carbon-50`) and dark (`--carbon-900`) modes.
- **Container**: `.container` limits content max-width to `1200px` and centers horizontally.

## Core Component Styles

### Header & Navigation (`header`)
- **Control Panel (`.control-panel`)**: Contains refresh interval selector, settings gear, and theme toggle button.
- **Settings Panel (`.settings-panel`)**: Absolutely positioned, floating below the gear icon, supporting language switching, history limit, page size, and other configuration items.

### Tab System (`.tabs`)
- Implements horizontally arranged tab navigation, supporting the `.active` class to highlight the currently selected module (Dashboard, Error Log, Task Injection).

### Common Card (`.card`)
- Has a unified background with rounded corners (`1rem`) and shadow effect.
- **Hover feedback**: Slight upward displacement (`translateY(-2px)`) on hover.

### Status Badge (`.badge`)
- Defines colored chip labels for different node running states (e.g., `.badge-running` is green).

## Utility Classes

- **Color classes**: Provides `.text-success` (green), `.text-error` (red), `.text-pending` (gray), `.text-duplicate` (orange) and other quick coloring classes.
- **Delta classes**: The `.text-delta-*` series is used in the dashboard to display lighter metric change values.
- **Hidden**: `.hidden` class for quickly controlling element visibility in JS.

## Modal Overlay (`.overlay`)

- **`.overlay`**: Fixed-position full-screen semi-transparent black overlay (`rgba(0,0,0,0.4)`), `z-index: 200`, centered flex layout, used to host modal windows like the card layout editor.
- **`.overlay.hidden`**: Sets the overlay to `display: none`, used with JS to control popup visibility.

## Card Layout Editor (`.layout-editor` series)

The card layout editor floats as a modal window above the overlay, supporting drag-and-drop rearrangement of three-column dashboard cards. Key sub-selectors:

| Selector | Description |
|--------|------|
| `.layout-editor` | Editor main container: rounded white-background card, `max-width: 700px`, vertical flex layout |
| `.dark-theme .layout-editor` | Dark mode uses `--carbon-800` background |
| `.layout-editor-header` | Title bar: left-right distribution, title on left, close button on right |
| `.layout-editor-title` | Title text: `1.1rem`, `font-weight: 600` |
| `.layout-editor-columns` | Three-column grid layout area: `grid-template-columns: repeat(3, 1fr)`, vertically scrollable |
| `.layout-column` | Single column container: vertical flex column |
| `.layout-column-header` | Column title: centered, underline separator, small font |
| `.layout-column-dropzone` | Drag drop zone: dashed border, min-height `120px`, vertical flex arrangement of cards |
| `.layout-column-dropzone.drag-over` | Drag hover highlight: blue border + light blue background |
| `.layout-card` | Draggable card item: gray background rounded, `cursor: grab`, `user-select: none` |
| `.layout-card:hover` | Hover float shadow effect |
| `.layout-card.dragging` | Semi-transparent during drag (`opacity: 0.5`) |
| `.layout-card-name` | Card name text: `0.8rem`, `font-weight: 500` |
| `.layout-card-handle` | Drag handle: ⠿ character, `color: --carbon-400` |
| `.layout-unused` | Unused card pool area: located below the three columns |
| `.layout-unused-header` | Unused pool title: `0.75rem`, gray |
| `.layout-unused .layout-column-dropzone` | Unused pool drop zone: horizontal arrangement (`flex-direction: row`), min-height `40px` |
| `.layout-editor-footer` | Bottom button bar: right-aligned, top separator line |
| `.btn-layout-save` | Save button: blue fill, occupies `80%` width |
| `.btn-layout-reset` | Reset button: gray outline, occupies `20%` width |
| `.btn-layout-editor` | Entry button in settings panel: blue fill, rounded |

## Responsive Rules

### `@media (max-width: 2048px)`

When viewport width ≤ 2048px, the following adjustments trigger:
- `h1` title width set to `100%`, preventing long title overflow
- `#theme-toggle` theme toggle button changes to `position: static`, `order: 3`, adapting to narrow-screen control bar reflow

## Dark Mode Adaptation

Uses the `.dark-theme` class as the root node identifier. In this mode, the system automatically adjusts:
- Background color and primary text color.
- Card and settings panel backgrounds and border colors.
- Form control (select, button) backgrounds and borders.
- Some semantic text colors (e.g., pending state text color).
