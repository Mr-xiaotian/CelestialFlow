# Card Layout Editor — `layout_editor`

> 📅 Last Updated: 2026/05/28

## Purpose

`layout_editor.ts` is the frontend module for the dashboard **card layout editor**. It provides a drag-and-drop interface within a floating window (overlay), allowing users to freely adjust which cards belong to the left, middle, and right columns of the dashboard, and persist the result to `config.json`.

The editor uses [SortableJS](https://sortablejs.github.io/Sortable/) to enable cross-zone drag-and-drop sorting, supporting moves between the three columns and the "unused card pool".

---

## Core Constants

### `DEFAULT_LAYOUT`

The default three-column card layout configuration, defining the factory card allocation scheme:

```javascript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis"],
  middle: ["status"],
  right:  ["progress", "summary"],
};
```

| Column | Default Cards | Description |
|--------|---------------|-------------|
| `left` | mermaid, analysis | Graph rendering + topology analysis |
| `middle` | status | Node status table |
| `right` | progress, summary | Progress + global summary |

---

## Core Functions

### `renderCard(cardId: string): HTMLElement`

Creates a draggable card DOM element.

| Parameter | Type | Description |
|-----------|------|-------------|
| `cardId` | `string` | Card identifier (e.g., `"mermaid"`, `"status"`) |

**Returns:** A `<div>` element with the `.layout-card` CSS class, a `data-card-id` attribute stored, and a drag handle.

```html
<div class="layout-card" data-card-id="mermaid">
  <span class="layout-card-name">Graph Rendering</span>
  <span class="layout-card-handle" aria-hidden="true">⠿</span>
</div>
```

The card name is looked up via `CARD_META[cardId]` for a localized display name, falling back to the raw `cardId`.

---

### `openLayoutEditor()`

Opens the layout editor and renders the current layout.

**Flow:**

```
┌──────────────────────────────────┐
│  1. Show overlay                 │
│  2. Read webConfig.dashboard     │
│     (use DEFAULT_LAYOUT if null) │
│  3. Save a copy to originalLayout│
│  4. Render left/middle/right     │
│     three columns                │
│  5. Render unused card pool      │
│  6. Call initSortable() to enable│
│     drag-and-drop                │
└──────────────────────────────────┘
```

The unused card pool contains all cards from `ALL_CARD_IDS` that are not referenced by any of the three columns.

---

### `closeLayoutEditor(restore: boolean = true)`

Closes the layout editor.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `restore` | `boolean` | `true` | Whether to restore original layout. When `true`, reverts all unsaved drag modifications; when `false`, retains current in-memory state |

**Behavior:**
- `restore=true` (default): Overwrites `webConfig.dashboard` with `originalLayout` and calls `applyConfig()` to refresh the dashboard. This is the behavior when clicking the close button or clicking the overlay.
- `restore=false`: Hides the overlay without restoring data. This is the behavior called after a successful save.

---

### `initSortable()`

Initializes SortableJS, enabling cross-zone drag-and-drop across the four drop zones.

**Zones Involved:**

| ID | Description |
|----|-------------|
| `layout-dropzone-left` | Left column drop zone |
| `layout-dropzone-middle` | Middle column drop zone |
| `layout-dropzone-right` | Right column drop zone |
| `layout-dropzone-unused` | Unused card pool |

**SortableJS Configuration:**

| Option | Value | Description |
|--------|-------|-------------|
| `group` | `"dashboard-layout"` | Shared group name, enabling cross-zone dragging |
| `animation` | `150` | Drag animation duration (ms) |
| `ghostClass` | `"dragging"` | CSS class for the drag placeholder |
| `dragClass` | `"dragging"` | CSS class for the card itself while dragging |

---

### `syncLayout()`

Syncs the current three-column card order from the DOM back to `webConfig.dashboard`.

**Flow:**
1. Iterates over the `left`, `middle`, `right` drop zones
2. Reads `data-card-id` from `.layout-card` elements in each zone
3. Writes the ordered arrays to `webConfig.dashboard`

> This function does **not persist**; it only updates the in-memory structure. Persistence is done by `saveLayout()`.

---

### `saveLayout()`

Saves the layout and refreshes the dashboard.

**Flow:**

```
┌───────────────────────────────────┐
│  1. syncLayout()                  │
│  2. await saveWebConfig()         │
│     ├─ Success → applyConfig()    │
│     │            closeLayoutEditor(false)
│     └─ Failure → Show save        │
│                  failure message  │
└───────────────────────────────────┘
```

`saveWebConfig()` persists `webConfig` to `config.json` via `POST /api/push_config`.

---

### `resetLayout()`

Resets the layout to `DEFAULT_LAYOUT`.

**Flow:**

1. Resets `webConfig.dashboard` to a deep copy of `DEFAULT_LAYOUT`
2. Clears and re-renders the left, middle, right columns (in default card order)
3. Clears and recalculates the unused card pool
4. Re-calls `initSortable()` to bind drag-and-drop

> This operation does **not auto-save**; the user must still click the save button to persist.

---

## Event Bindings

The module binds the following events on `DOMContentLoaded`:

| Target Element | Event | Handler |
|----------------|-------|---------|
| `#open-layout-editor` | `click` | `openLayoutEditor()` |
| `#layout-editor-close` | `click` | `closeLayoutEditor()` (restore) |
| `#layout-editor-overlay` | `click` | `closeLayoutEditor()` (restore) on overlay outer click |
| `#layout-save-btn` | `click` | `saveLayout()` |
| `#layout-reset-btn` | `click` | `resetLayout()` |

---

## Usage Example

### HTML Structure

The layout editor depends on the following DOM structure:

```html
<!-- Trigger button -->
<button id="open-layout-editor">Edit Layout</button>

<!-- Overlay -->
<div id="layout-editor-overlay" class="hidden">
  <div class="layout-editor-panel">
    <h2>Card Layout</h2>

    <!-- Three-column drop zones -->
    <div id="layout-dropzone-left"></div>
    <div id="layout-dropzone-middle"></div>
    <div id="layout-dropzone-right"></div>

    <!-- Unused card pool -->
    <div id="layout-dropzone-unused"></div>

    <!-- Action buttons -->
    <button id="layout-save-btn">Save</button>
    <button id="layout-reset-btn">Reset</button>
    <button id="layout-editor-close">Close</button>
  </div>
</div>
```

### Customizing the Default Layout

Modify the `DEFAULT_LAYOUT` constant to change the factory layout:

```typescript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis", "custom-card"],
  middle: ["status", "errors"],
  right:  ["progress"],
};
```
