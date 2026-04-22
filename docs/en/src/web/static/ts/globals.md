# globals.d.ts

> 📅 Last updated: 2026/04/22

TypeScript global type declaration file that provides type declarations for third-party libraries included via CDN `<script>` tags, preventing compilation errors.

## Declaration Contents

```ts
declare const Chart: any;    // Chart.js — Line charts
declare const Sortable: any; // SortableJS — Drag-and-drop sorting

interface Window {
  mermaid: any; // Mermaid — Flowchart rendering
}
```

## Description

All three libraries are mounted to the global scope via CDN `<script>` tags in `index.html`:

- `Chart.js` → `window.Chart`, used for line charts in `task_history.ts`
- `SortableJS` → `window.Sortable`, used for drag-and-drop sorting of stage cards in `task_statuses.ts`
- `mermaid` → `window.mermaid`, used for task graph visualization in `task_structure.ts`, loaded via ESM dynamic import

This file contains no runtime code and only takes effect during TypeScript compilation.
