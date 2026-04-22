# task_structure.ts

> 📅 Last updated: 2026/04/22

Manages the loading of task graph structure data and on-demand rendering of Mermaid flowcharts.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `structureData` | `any[]` | Task graph root node array fetched from the backend |
| `structureRev` | `number` | Version number from the last fetch, used for incremental fetching (`known_rev`) |

## Functions

### `loadStructure()`

Asynchronously fetches the graph structure array from `GET /api/pull_structure?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `structureData` and `structureRev`, returning `true`.

---

### `getNodeId(node)`

Replaces non-word characters in the node name with `_` to generate a Mermaid-compatible node ID.

---

### `getShapeWrappedLabel(label, shape)`

Generates Mermaid node label syntax based on shape type.

| `shape` Value | Mermaid Syntax | Purpose |
|--------------|----------------|---------|
| `box` (default) | `[label]` | Standard rectangle node |
| `round` | `(label)` | Rounded rectangle |
| `circle` | `((label))` | Circle |
| `rhombus` | `{{label}}` | Diamond (Router node) |
| `subgraph` | `[[label]]` | Subroutine box (Splitter node) |
| `parallelogram` | `[/label/]` | Parallelogram (Redis transport node) |
| `db` | `[(label)]` | Database cylinder |
| `hex` | `{{{label}}}` | Hexagon |
| `arrow` | `>label]` | Arrow shape |

---

### `renderMermaidStructure(statuses?)`

Builds Mermaid code from `structureData` and the passed `statuses` (`Record<string, NodeStatus>`, defaults to empty object) and renders it to the DOM.

**Flow:**

1. Traverses `structureData` (DFS `walk()`):
   - Determines node shape based on `func_name` (`_split` → subgraph, `_route` → rhombus, `_transport/_source/_ack` → parallelogram)
   - Determines node style class based on `nodeStatuses[tag].status` (`greenNode` / `greyNode` / `whiteNode`)
   - Collects all edges (deduplicated via Set)
2. Selects `classDef` color scheme based on current theme
3. Generates `graph TD` Mermaid code
4. Creates a new `<div>` to replace the old `#mermaid-container` and calls `window.mermaid.run()` to render

**Node Status Colors:**

| `status` | Style Class | Meaning |
|----------|-------------|---------|
| `1` | `greenNode` | Running |
| `2` | `greyNode` | Stopped |
| No data | `whiteNode` | Not started |
