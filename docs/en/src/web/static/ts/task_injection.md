# task_injection.ts

> 📅 Last Updated: 2026/04/22

Task injection page logic, supporting node selection, task data input (JSON text or file upload), and submission to the backend.

## Type Definitions

```ts
type SelectedNode = { name: string; type: string; status?: number };
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `selectedNodes` | `SelectedNode[]` | Currently selected node list |
| `currentInputMethod` | `string` | Current input method: `"json"` or `"file"` |
| `uploadedFile` | `{name, content} \| null` | Uploaded JSON file content |

## Functions

### `setupEventListeners()`

Binds page events: search input, real-time JSON textarea validation, file selection, submit button.

---

### `renderNodeList(searchTerm?)`

Renders the node selection list.

- Filters node names based on `searchTerm`
- Reads node statuses from `nodeStatuses` and renders badges
- Nodes with status `2` (stopped) are disabled for clicking (`disabled-node` style)

---

### `selectNode(nodeName)` / `removeNode(nodeName)`

Toggles node selection state (clicking an already selected node deselects it), and calls `updateSelectedNodes()` to refresh the selected list UI.

---

### `selectAllNodes()`

Selects all nodes with `status !== 2` (excludes stopped nodes).

---

### `clearSelection()`

Clears all selected nodes.

---

### `switchInputMethod(method)`

Switches the input method (`"json"` / `"file"`), updating the corresponding area's visibility and button active state.

---

### `fillTermination()`

Fills the JSON textarea with a predefined termination signal `["TERMINATION_SIGNAL"]`, allowing users to quickly inject a termination signal.

---

### `handleFileUpload(e)`

Handles file upload: accepts only `.json` format, reads and validates JSON validity, and saves to `uploadedFile`.

---

### `handleSubmit()`

Submits task injection.

1. Validates selected nodes (at least one)
2. Parses task data based on input method
3. POSTs to `/api/push_injection_tasks` for each selected node sequentially, then displays a success message after all complete
4. Calls `clearForm()` to reset the form

---

### Helper Functions

| Function | Description |
|----------|-------------|
| `showError(elementId, message)` | Displays error prompt text |
| `hideError(elementId)` | Hides error prompt |
| `showStatus(message, isSuccess)` | Displays operation result message (auto-hides after 3 seconds) |
| `setButtonLoading(loading)` | Toggles submit button loading state |
| `clearForm()` | Resets all selections, inputs, and error prompts |

## Task Injection Request Body

```json
{
    "node": "stage_tag",
    "task_datas": [...],
    "timestamp": "2024-01-01T00:00:00.000Z"
}
```

POSTed to `POST /api/push_injection_tasks`. The server stores it in the `injection_tasks` queue, which is periodically pulled by `TaskReporter` via `GET /api/pull_task_injection` and injected into the `TaskGraph`.
