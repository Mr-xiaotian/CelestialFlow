# base.css

> Last Updated: 2026/05/28

Manages the system's global base styles, dark mode switching, common components (cards, tabs, badges), responsive base layout, and card layout editor modal styles.

## Global Base

- **Reset**: Unified box model (`border-box`) and default font sequence.
- **Background & Color**: Defines body background colors for light (`--carbon-50`) and dark (`--carbon-900`) modes.
- **Container**: `.container` limits content max-width to `1200px` and centers horizontally.

## Core Component Styles

### Header & Navigation (`header`)
- **Control Panel (`.control-panel`)**: Contains refresh interval selector, settings gear, and theme toggle button.
- **Settings Panel (`.settings-panel`)**: Absolutely positioned floating below the gear icon, supports language switching, history limit, page size, and other configuration items.

### Tab System (`.tabs`)
- Implements horizontally arranged tab navigation, supporting `.active` class to highlight the currently selected module (Dashboard, Error Logs, Task Injection).

### Common Card (`.card`)
- Has unified background rounded corners (`1rem`) and shadow effects.
- **Hover Feedback**: Produces a slight upward displacement (`translateY(-2px)`) on hover.

### Status Badge (`.badge`)
- Defines colored block labels for nodes in different running states (e.g., `.badge-running` is green).

## Helper Classes

- **Color Classes**: Provides quick coloring classes like `.text-success` (green), `.text-error` (red), `.text-pending` (gray), `.text-duplicate` (orange).
- **Delta Classes**: `.text-delta-*` series for displaying lighter metric change values in the dashboard.
- **Hidden**: `.hidden` class for quickly controlling element visibility in JS.

## Modal Overlay (`.overlay`)

- **`.overlay`**: Fixed position full-screen semi-transparent black overlay (`rgba(0,0,0,0.4)`), `z-index: 200`, centered flex layout, used to host modal windows like the card layout editor.
- **`.overlay.hidden`**: Sets the overlay to `display: none`, used with JS to control modal visibility.

## Card Layout Editor (`.layout-editor` Series)

The card layout editor appears as a modal window floating above the overlay, supporting drag-and-drop reordering of the three-column dashboard cards. Main sub-selectors:

| Selector | Description |
|----------|-------------|
| `.layout-editor` | Editor main container: rounded white-background card, `max-width: 700px`, vertical flex layout |
| `.dark-theme .layout-editor` | Uses `--carbon-800` background in dark mode |
| `.layout-editor-header` | Title bar: left-right distribution, title on left, close button on right |
| `.layout-editor-title` | Title text: `1.1rem`, `font-weight: 600` |
| `.layout-editor-columns` | Three-column grid layout area: `grid-template-columns: repeat(3, 1fr)`, vertically scrollable |
| `.layout-column` | Single column container: vertical flex column |
| `.layout-column-header` | Column title: centered, underline separator, small font |
| `.layout-column-dropzone` | Drag-and-drop zone: dashed border, minimum height `120px`, vertical flex arrangement of cards |
| `.layout-column-dropzone.drag-over` | Highlight on drag hover: blue border + light blue background |
| `.layout-card` | Draggable card item: gray background rounded corners, `cursor: grab`, `user-select: none` |
| `.layout-card:hover` | Floating shadow effect on hover |
| `.layout-card.dragging` | Semi-transparent (`opacity: 0.5`) while dragging |
| `.layout-card-name` | Card name text: `0.8rem`, `font-weight: 500` |
| `.layout-card-handle` | Drag handle: ⠿ character, `color: --carbon-400` |
| `.layout-unused` | Unused card pool area: located below the three columns |
| `.layout-unused-header` | Unused pool title: `0.75rem`, gray |
| `.layout-unused .layout-column-dropzone` | Unused pool drop zone: horizontal arrangement (`flex-direction: row`), minimum height `40px` |
| `.layout-editor-footer` | Footer button bar: right-aligned, top separator line |
| `.btn-layout-save` | Save button: blue fill, `80%` width |
| `.btn-layout-reset` | Reset button: gray outline, `20%` width |
| `.btn-layout-editor` | Entry button in settings panel: blue fill, rounded corners |

## Responsive Rules

### `@media (max-width: 2048px)`

Triggers the following adjustments when viewport width ≤ 2048px:
- `h1` title width set to `100%`, preventing long title overflow
- `#theme-toggle` theme toggle button changed to `position: static`, `order: 3`, adapting the control bar reordering for narrow screens

## Dark Mode Adaptation

Uses the `.dark-theme` class as the root node identifier. In this mode, the system automatically adjusts the following properties:
- Background color and main text color.
- Card and settings panel background and border colors.
- Form control (select, button) background and border.
- Some semantic text colors (such as the pending status text color).
