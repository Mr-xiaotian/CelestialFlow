# injection_layout.css

> 📅 Last Updated: 2026/06/22

Defines styles for the task injection page's search/filter, two-column layout, and responsive breakpoint styles.

## Two-Column Layout (`.card-grid`)

```css
.card-grid {
  display: grid;
  grid-template-columns: minmax(18rem, 22rem) minmax(0, 1fr);
  gap: 1.5rem;
}
```

- Left node list is fixed at 18–22rem, right editor fills the remaining width.

## Search Filter

- **Search Container (`.search-container`)**: Relative positioning, used to host the search icon.
- **Search Input (`.search-input`)**:
  - Left padding `2.5rem` reserves space for the search icon.
  - Border color switches to `--cornflower-400` on focus.
  - Dark mode: `--carbon-700` background.
- **Search Icon (`.search-icon`)**: Absolute positioned on the left side of the input, `1rem`, `color: --carbon-400`.

## Injectable Node Toggle (`.injectable-toggle`)

- `flex` layout, `gap: 0.5rem`, `font-size: 0.75rem`.
- Located below the search box, above the node list.

## Responsive (`@media (max-width: 2048px)`)

On narrow screens (≤2048px):
- `.card-grid` switches to single column (`grid-template-columns: 1fr`).
- `.node-list` removes `max-height` restriction.
- `.editor-header` and `.submit-section` switch to vertical stacking.
- `.editor-actions` switches to vertical layout.

## Related Modules

- Layout structure is dynamically populated by `renderInjectionPage()` in `injection.ts`.
- Search and filter events are bound by `setupEventListeners()`.
