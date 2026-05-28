# dashboard_analysis.ts

> 📅 Last Updated: 2026/05/28

Manages loading of graph analysis information and rendering of the analysis panel. Provides deep insights into the TaskGraph topology, such as cycle detection and layer analysis.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `analysisData` | `Record<string, any>` | Analysis data, containing graph structure type, DAG status, etc. |
| `analysisRev` | `number` | Data version number, used for incremental fetch decisions |

## Functions

### `loadAnalysis()`

Asynchronously fetches analysis data from `GET /api/pull_analysis?known_rev=N`.

---

### `renderAnalysisInfo()`

Renders analysis data to the `#analysis-info` container. If data is empty, displays "No analysis information available".

**Display Fields:**

| Display Label | Corresponding Field | Description |
|---------------|---------------------|-------------|
| `Structure Type` | `className` | Specific Python class name of the TaskGraph |
| `Is DAG` | `isDAG` | Whether it is a directed acyclic graph; shows yellow warning style when not a DAG |
| `Schedule Mode` | `scheduleMode` | `eager` or `staged` |
| `Layer Count` | `layersDict` | Topological layering depth of the graph |

## Data Flow

```
GET /api/pull_analysis
  └─ loadAnalysis() -> Update analysisData
        └─ renderAnalysisInfo() -> UI list display
```

## Usage Example

### Analysis Data Structure and Rendering Call Chain

The following example shows the structure of analysis data on the TypeScript side and the rendering flow:

```typescript
// Typical structure of analysis data (from backend GET /api/pull_analysis)
// Note: The backend returns snake_case fields; the frontend converts to camelCase on receipt
const analysisPayload = {
    analysis: {
        className: "TaskGraph",
        isDAG: true,
        scheduleMode: "eager",
        layersDict: {0: ["StageA"], 1: ["StageB", "StageC"], 2: ["StageD"]},
    }
};

// This data is processed and rendered through the following chain:

// 1. loadAnalysis() fetches and updates global variables
// analysisData structure: Record<string, any>
// e.g.: { className, isDAG, scheduleMode, layersDict }

// 2. renderAnalysisInfo() renders it to the #analysis-info container
//    Actual rendering logic (illustrative):
function renderAnalysisInfoExample(data: Record<string, any>) {
    const container = document.getElementById("analysis-info");
    if (!container) return;

    if (!data || Object.keys(data).length === 0) {
        container.innerHTML = "<p>No analysis information available</p>";
        return;
    }

    container.innerHTML = `
        <div class="analysis-item">
            <span class="analysis-label">Structure Type</span>
            <span class="analysis-value">${escapeHtml(data.className || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">Is DAG</span>
            <span class="analysis-value ${data.isDAG ? '' : 'warning'}">
                ${data.isDAG ? "Yes (acyclic)" : "No (cycles exist)"}
            </span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">Schedule Mode</span>
            <span class="analysis-value">${escapeHtml(data.scheduleMode || "-")}</span>
        </div>
        <div class="analysis-item">
            <span class="analysis-label">Layer Count</span>
            <span class="analysis-value">
                ${data.layersDict ? Object.keys(data.layersDict).length : 0}
            </span>
        </div>
    `;
}

// 3. Complete call chain
async function fullAnalysisFlow() {
    // Call fetch to pull data
    const res = await fetch("/api/pull_analysis?known_rev=0");
    const data = await res.json();

    // Update global cache
    // analysisData = data; (maintained internally by loadAnalysis)
    // analysisRev = data.rev ?? 0;

    // Trigger rendering
    renderAnalysisInfoExample(data);
}
```
