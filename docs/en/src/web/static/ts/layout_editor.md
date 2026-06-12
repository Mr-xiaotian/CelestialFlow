# Card Layout Editor — `layout_editor`

> 📅 Last Updated: 2026/05/28

## Purpose

`layout_editor.ts` is the frontend module for the dashboard **card layout editor**. It provides a drag-and-drop interface within a floating overlay window, allowing users to freely adjust which cards belong to the dashboard's left, middle, and right columns, and persist the result to `config.json`.

The editor uses [SortableJS](https://sortablejs.github.io/Sortable/) to enable cross-zone drag-and-drop sorting, supporting mutual drag between the three columns and an "unused card pool".

---

## Core Constants

### `DEFAULT_LAYOUT`

The default three-column card layout configuration, defining the system's factory card allocation:

```javascript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis"],
  middle: ["status"],
  right:  ["progress", "summary"],
};
```

| Column | Default Cards | Description |
|------|----------|------|
| `left` | mermaid, analysis | Graph rendering + topology analysis |
| `middle` | status | Node status table |
| `right` | progress, summary | Progress + global summary |

---

## Core Functions

### `renderCard(cardId: string): HTMLElement`

Creates a draggable card DOM element.

| Parameter | Type | Description |
|------|------|------|
| `cardId` | `string` | Card identifier (e.g., `"mermaid"`, `"status"`) |

**Returns:** A `<div>` element with the `.layout-card` CSS class, storing a `data-card-id` attribute and a drag handle.

```html
<div class="layout-card" data-card-id="mermaid">
  <span class="layout-card-name">Graph Rendering</span>
  <span class="layout-card-handle" aria-hidden="true">⠿</span>
</div>
```

The card name is looked up via `CARD_META[cardId]` for a localized display name, falling back to the raw `cardId` if not found.

---

### `openLayoutEditor()`

Opens the layout editor and renders the current layout.

**Flow:**

```
┌──────────────────────────────────┐
│  1. Show overlay                 │
│  2. Read webConfig.dashboard     │
│     (fallback to DEFAULT_LAYOUT) │
│  3. Save a copy to originalLayout│
│  4. Render left/middle/right     │
│     columns                      │
│  5. Render unused card pool      │
│  6. Call initSortable() to       │
│     enable drag-and-drop         │
└──────────────────────────────────┘
```

The unused card pool contains all cards from `ALL_CARD_IDS` not referenced by the three columns.

---

### `closeLayoutEditor(restore: boolean = true)`

Closes the layout editor.

| Parameter | Type | Default | Description |
|------|------|--------|------|
| `restore` | `boolean` | `true` | Whether to restore the original layout. `true` reverts all unsaved drag modifications; `false` preserves the current in-memory state |

**Behavior:**
- `restore=true` (default): Overwrites `webConfig.dashboard` with `originalLayout` and calls `applyConfig()` to refresh the dashboard. This is the behavior when clicking the close button or clicking the overlay backdrop.
- `restore=false`: Hides the overlay without restoring data. This is the behavior called after a successful save.

---

### `initSortable()`

Initializes SortableJS, enabling cross-zone drag-and-drop across four drop zones.

**Zones involved:**

| ID | Description |
|----|------|
| `layout-dropzone-left` | Left column drop zone |
| `layout-dropzone-middle` | Middle column drop zone |
| `layout-dropzone-right` | Right column drop zone |
| `layout-dropzone-unused` | Unused card pool |

**SortableJS configuration:**

| Option | Value | Description |
|--------|-----|------|
| `group` | `"dashboard-layout"` | Shared group name, four zones can inter-drag |
| `animation` | `150` | Drag animation duration (ms) |
| `ghostClass` | `"dragging"` | CSS class for the ghost placeholder during drag |
| `dragClass` | `"dragging"` | CSS class for the card itself during drag |

---

### `syncLayout()`

Syncs the current three-column card ordering from the DOM back into `webConfig.dashboard`.

**Flow:**
1. Iterates through the `left`, `middle`, `right` three drop zones
2. Reads `data-card-id` from each zone's `.layout-card` elements
3. Writes them as ordered arrays into `webConfig.dashboard`

> This function **does not persist**; it only updates the in-memory structure. Persistence is handled by `saveLayout()`.

---

### `saveLayout()`

Saves the layout and refreshes the dashboard.

**Flow:**

```
┌───────────────────────────────────┐
│  1. syncLayout()                  │
│  2. await saveWebConfig()         │
│     ├─ success → applyConfig()    │
│     │         closeLayoutEditor(false)
│     └─ failure → show save        │
│                  failure message  │
└───────────────────────────────────┘
```

`saveWebConfig()` persists `webConfig` to `config.json` via `POST /api/push_config`.

---

### `resetLayout()`

Resets the layout to `DEFAULT_LAYOUT`.

**Flow:**

1. Resets `webConfig.dashboard` to a deep copy of `DEFAULT_LAYOUT`
2. Clears and re-renders the left/middle/right columns (in default card order)
3. Clears and recalculates the unused card pool
4. Re-calls `initSortable()` to bind drag-and-drop

> This operation **does not auto-save**; the user must still click the save button to persist.

---

## Event Bindings

The module binds the following events on `DOMContentLoaded`:

| Target Element | Event | Handler |
|----------|------|----------|
| `#open-layout-editor` | `click` | `openLayoutEditor()` |
| `#layout-editor-close` | `click` | `closeLayoutEditor()` (restore) |
| `#layout-editor-overlay` | `click` | Clicking the overlay backdrop triggers `closeLayoutEditor()` (restore) |
| `#layout-save-btn` | `click` | `saveLayout()` |
| `#layout-reset-btn` | `click` | `resetLayout()` |

---

## Usage Example

### HTML Structure

The layout editor depends on the following DOM structure:

```html
<!-- Trigger button -->
<button id="open-layout-editor">Edit Layout</button>

<!-- Overlay layer -->
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

### Custom Default Layout

Modify the `DEFAULT_LAYOUT` constant to change the factory layout:

```typescript
const DEFAULT_LAYOUT = {
  left:   ["mermaid", "analysis", "custom-card"],
  middle: ["status", "errors"],
  right:  ["progress"],
};
```
