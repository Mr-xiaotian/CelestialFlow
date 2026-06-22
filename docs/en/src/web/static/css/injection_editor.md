# injection_editor.css

> 📅 Last Updated: 2026/06/22

Defines styles for the right-side editor panel of the task injection page, including the JSON input area, validation messages, and action button groups.

## Editor Container (`.injection-editor-card`)

- Uses vertical flex layout with a fixed gap of `gap: 1rem`.

## Editor Header (`.editor-header`)

- **Layout**: `flex` left-right distribution — left side has description text + current node info, right side has action button group.
- `.editor-node-meta`: Allows shrinking in narrow widths (`min-width: 0`).
- `.editor-caption`: Small caption text above the "Current Node" title, `0.75rem`, gray tone (`--carbon-500`).

## Current Node Info (`.editor-node-row`)

- Row layout of node name and the right-side "Edited" badge, supports `flex-wrap: wrap`.
- `.current-node-name`: Currently selected node name, `1rem`, `font-weight: 600`.

## Button Styles (`.btn-small`, `.btn-select`, `.btn-clear`)

| Selector | Purpose | Background | Text Color |
|----------|---------|------------|------------|
| `.btn-small` | General small button | — | — |
| `.btn-select` | Validate/Format button | `--cornflower-50` (light) / `--cornflower-700` (dark) | `--cornflower-700` (light) / `--carbon-100` (dark) |
| `.btn-clear` | Clear draft button | `--carbon-100` (light) / `--carbon-600` (dark) | `--carbon-700` (light) / `--carbon-100` (dark) |

- **Disabled state**: `opacity: 0.6`, `cursor: not-allowed`.

## JSON Input Area (`.json-input-section`)

- **JSON Header (`.json-header`)**: Label and "Fill termination template" button distributed left and right.
- **JSON Label (`.json-label`)**: `0.75rem`, `font-weight: 500`.
- **Template Button (`.example-btn`)**: Backgroundless text button, `color: --cornflower-500`, darkens on hover.
- **JSON Editor (`.json-textarea`)**:
  - Monospace font (`Monaco, Menlo, monospace`), `min-height: 20rem`, supports vertical resizing.
  - Border changes to `--cornflower-400` on focus.
  - Disabled state: `--carbon-50` background, `--carbon-400` text.

## Validation Message (`.validation-message`)

| State | CSS Class | Color |
|-------|-----------|-------|
| Success | `.validation-success` | `--jade-600` (light) / `--jade-400` (dark) |
| Failure | `.validation-error` | `--crimson-600` (light) / `--crimson-400` (dark) |
| Neutral | `.validation-neutral` | `--carbon-500` (light) / `--carbon-400` (dark) |

- `min-height: 1.25rem`, `font-size: 0.75rem`, located below the JSON editor.

## Editor Bottom Button Group (`.editor-actions`)

- `flex` layout, `gap: 0.75rem`, `flex-wrap: wrap`.

## Related Modules

- Interaction logic is driven by functions in `injection.ts`: `renderCurrentNodeEditor()`, `validateCurrentDraft()`, `formatCurrentDraft()`, etc.
- The "Fill termination template" button is handled by `fillTerminationDraft()`.
