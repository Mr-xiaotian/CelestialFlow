# task_analysis.ts

> 📅 Last Updated: 2026/04/22

Manages loading of graph analysis information and rendering of the analysis panel.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `analysisData` | `Record<string, any>` | Analysis data fetched from the backend |
| `analysisRev` | `number` | Last fetched version number, used for incremental fetching (`known_rev`) |

## Functions

### `loadAnalysis()`

Asynchronously fetches analysis data from `GET /api/pull_analysis?known_rev=N`. If the server data has not changed (`body.data === null`), returns `false`; otherwise updates `analysisData` and `analysisRev`, and returns `true`.

---

### `renderAnalysisInfo()`

Renders analysis data to the `#analysis-info` container.

If data is empty, displays placeholder text "No analysis information available".

**Displayed fields:**

| `analysisData` Field | Display Label | Description |
|---------------------|---------------|-------------|
| `class_name` | Structure Type | TaskGraph topology class name (e.g., TaskChain, TaskLoop, etc.) |
| `isDAG` | Is DAG | Boolean, displays "Yes (acyclic)" or "No (cycles exist)" with color markers |
| `schedule_mode` | Schedule Mode | `eager` or `staged` |
| `layers_dict` | Layer Count | `Object.keys(layers_dict).length` gives the number of layers |

When `isDAG` is `true`, the text has the `ok` (green) style; when `false`, it has the `warn` (orange) style.
