# globals.d.ts

> 📅 Last Updated: 2026/04/22

TypeScript global type declaration file that provides type declarations for third-party libraries loaded via CDN `<script>` tags, preventing compilation errors.

## Declarations

```ts
declare const Chart: any;    // Chart.js — line charts
declare const Sortable: any; // SortableJS — drag-and-drop sorting

interface Window {
  mermaid: any; // Mermaid — flowchart rendering
}
```

## Description

These three libraries are all mounted globally via CDN `<script>` tags in `index.html`:

- `Chart.js` → `window.Chart`, used for line charts in `task_history.ts`
- `SortableJS` → `window.Sortable`, used for node card drag-and-drop sorting in `task_statuses.ts`
- `mermaid` → `window.mermaid`, used for task graph visualization in `task_structure.ts`, loaded via ESM dynamic import

This file contains no runtime code and only takes effect during the TypeScript compilation phase.
