# task_structure.ts

> 📅 Last Updated: 2026/04/22

Manages loading of task graph structure data and on-demand rendering of Mermaid flowcharts.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `structureData` | `any[]` | Task graph root node array, fetched from backend |
| `structureRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |

## Functions

### `loadStructure()`

Asynchronously fetches graph structure array from `GET /api/pull_structure?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `structureData` and `structureRev`, and returns `true`.

---

### `getNodeId(node)`

Replaces non-word characters in the node name with `_` to generate a Mermaid-compatible node ID.

---

### `getShapeWrappedLabel(label, shape)`

Generates Mermaid node label syntax based on the shape type.

| `shape` Value | Mermaid Syntax | Usage |
|--------------|----------------|-------|
| `box` (default) | `[label]` | Regular rectangle node |
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

Builds Mermaid code from `structureData` and the provided `statuses` (`Record<string, NodeStatus>`, defaults to empty object) and renders to DOM.

**Flow:**

1. Iterate over `structureData` (DFS `walk()`):
   - Determine node shape based on `func_name` (`_split` → subgraph, `_route` → rhombus, `_transport/_source/_ack` → parallelogram)
   - Determine node style class based on `nodeStatuses[tag].status` (`greenNode` / `greyNode` / `whiteNode`)
   - Collect all edges (deduplicated via Set)
2. Choose `classDef` color scheme based on current theme
3. Generate `graph TD` Mermaid code
4. Create a new `<div>` to replace the old `#mermaid-container` and call `window.mermaid.run()` to render

**Node status colors:**

| `status` | Style Class | Meaning |
|----------|-------------|---------|
| `1` | `greenNode` | Running |
| `2` | `greyNode` | Stopped |
| No data | `whiteNode` | Not started |
