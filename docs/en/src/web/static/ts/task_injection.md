# task_injection.ts

> 📅 Last updated: 2026/04/22

Logic for the task injection page, supporting stage selection, task data input (JSON text or file upload), and submission to the backend.

## Type Definitions

```ts
type SelectedNode = { name: string; type: string; status?: number };
```

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `selectedNodes` | `SelectedNode[]` | Currently selected stage list |
| `currentInputMethod` | `string` | Current input method: `"json"` or `"file"` |
| `uploadedFile` | `{name, content} \| null` | Uploaded JSON file content |

## Functions

### `setupEventListeners()`

Binds page events: search box input, JSON textarea real-time validation, file selection, submit button.

---

### `renderNodeList(searchTerm?)`

Renders the stage selection list.

- Filters stage names based on `searchTerm`
- Reads stage status from `nodeStatuses` and renders badges
- Stages with status `2` (stopped) are disabled (styled with `disabled-node`)

---

### `selectNode(nodeName)` / `removeNode(nodeName)`

Toggles stage selection state (clicking an already selected stage deselects it), then calls `updateSelectedNodes()` to refresh the selected list UI.

---

### `selectAllNodes()`

Selects all stages with `status !== 2` (excludes stopped stages).

---

### `clearSelection()`

Clears all selected stages.

---

### `switchInputMethod(method)`

Switches input method (`"json"` / `"file"`), updating the visibility of corresponding areas and button active states.

---

### `fillTermination()`

Fills the JSON textarea with the predefined termination signal `["TERMINATION_SIGNAL"]`, providing a quick way for users to inject a termination signal.

---

### `handleFileUpload(e)`

Handles file uploads: accepts only `.json` format files, reads and validates JSON validity, and saves to `uploadedFile`.

---

### `handleSubmit()`

Submits the task injection.

1. Validates selected stages (at least one required)
2. Parses task data based on the input method
3. POSTs to `/api/push_injection_tasks` for each selected stage; displays a success message after all complete in parallel
4. Calls `clearForm()` to reset the form

---

### Helper Functions

| Function | Description |
|----------|-------------|
| `showError(elementId, message)` | Displays error message text |
| `hideError(elementId)` | Hides error message |
| `showStatus(message, isSuccess)` | Displays operation result message (auto-hides after 3 seconds) |
| `setButtonLoading(loading)` | Toggles the submit button loading state |
| `clearForm()` | Resets all selections, inputs, and error messages |

## Task Injection Request Body

```json
{
    "node": "stage_tag",
    "task_datas": [...],
    "timestamp": "2024-01-01T00:00:00.000Z"
}
```

POSTed to `POST /api/push_injection_tasks`; the server stores it in the `injection_tasks` queue, which `TaskReporter` periodically pulls via `GET /api/pull_task_injection` and injects into the `TaskGraph`.
