# injection_preview.css

> 📅 Last Updated: 2026/06/22

Defines styles for the bottom draft preview area, submit button, status messages, and loading animation of the task injection page.

## Draft Preview Card (`.draft-card`)

- Vertical flex layout, `gap: 0.75rem`, `margin-bottom: 1rem`.
- Serves as the aggregated display area for all edited drafts.

## Draft Preview Area (`.draft-preview`)

- **Read-only style**: `margin: 0`, `padding: 1rem`, no input state.
- **Monospace font**: `Monaco, Menlo, monospace`, `font-size: 0.75rem`.
- **Background**: Light mode `--carbon-50`, dark mode `--carbon-800`.
- **Overflow**: `overflow: auto`, supports scrolling for long content.
- **Min height**: `min-height: 12rem`.

## Empty State Placeholder (`.empty-placeholder`)

- Shown when there are no drafts, uses monospace font style.

## Submit Section (`.submit-section`)

- `flex` layout, left-right distribution (status hint + submit button), `gap: 1rem`, `margin-top: auto`.

## Status Message (`.status-message`)

- `flex` layout, `align-items: center`, `font-weight: 500`.

| CSS Class | Description | Color |
|-----------|-------------|-------|
| `.status-success` | Submit success | `--jade-600` (light) / `--jade-400` (dark) |
| `.status-error` | Submit failure | `--crimson-600` (light) / `--crimson-400` (dark) |

- **Status Icon (`.status-icon`)**: `1.25rem`, right margin `0.5rem`, reserved for inline SVG icons.

## Submit Button (`.btn-submit`)

- **Base style**: Blue fill (`--cornflower-500`), white text, rounded `0.5rem`, with shadow.
- **Hover effect**: Background deepens (`--cornflower-600`), slight upward shift `-1px`.
- **Disabled state**: `--carbon-400` background, `cursor: not-allowed`, no shadow or displacement.
- **Dark mode**: Background `--cornflower-600`, disabled state `--carbon-500`.

## Loading Indicator (`.spinner`)

```css
.spinner {
  width: 1rem;
  height: 1rem;
  border: 2px solid var(--frost-0);
  border-top: 2px solid transparent;
  border-radius: 50%;
  animation: injection-spin 1s linear infinite;
}
```

- Dynamically inserted inside the submit button during submission, white ring + transparent top rotation effect.

## Spin Animation (`@keyframes injection-spin`)

```css
@keyframes injection-spin {
  0%   { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
```

## Related Modules

- Draft preview is dynamically rendered by `renderDraftList()` in `injection.ts`.
- Submit interaction is driven by `handleSubmit()` (button loading state toggle, status message display).
- Submit button availability is controlled by `updateSubmitButtonAvailability()`.
