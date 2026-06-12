# _colors.css

> 📅 Last Updated: 2026/05/23

Defines the global color system variables used by the Web UI, implemented via CSS Variables (`:root`) for unified management and theme switching.

## Color System

The project uses a multi-shade design, each color family containing multiple shades from 50 to 900.

### Core Color Families

- **Frost**: `--frost-0` (#ffffff). Used for backgrounds and pure white elements.
- **Carbon**: `--carbon-50` ~ `--carbon-900`. Used for text, borders, shadows, and dark mode backgrounds.
- **Jade**: `--jade-50` ~ `--jade-900`. Used for success status, progress bars, and positive feedback.
- **Crimson**: `--crimson-50` ~ `--crimson-900`. Used for error status, exception alerts, and negative feedback.
- **Marigold**: `--marigold-50` ~ `--marigold-900`. Used for duplicate tasks, warnings, and neutral status.
- **Cornflower**: `--cornflower-50` ~ `--cornflower-900`. Used for running status, links, and primary action buttons.

### Auxiliary Color Families

- **Amber**: `--amber-50` ~ `--amber-900`.
- **Rose**: `--rose-50` ~ `--rose-900`.
- **Violet**: `--violet-50` ~ `--violet-900`.
- **Sky**: `--sky-50` ~ `--sky-900`.

## Usage

Reference via the `var()` function in other CSS files:

```css
.example {
  color: var(--carbon-900);
  background-color: var(--jade-50);
  border: 1px solid var(--cornflower-500);
}
```

## Design Guidelines

- **Text color**: Default uses `--carbon-900` (light mode) or `--carbon-200` (dark mode).
- **Border color**: Commonly uses `--carbon-200` or `--carbon-300`.
- **Status colors**:
  - Success: `Jade`
  - Error: `Crimson`
  - Duplicate: `Marigold`
  - Running: `Cornflower`
  - Pending/Stopped: `Carbon`
