# injection.ts

> 📅 Last Updated: 2026/05/28

Manages the task manual injection page logic, supporting multi-node selection, JSON text input, JSON file upload, termination signal quick fill, and injection submission.

## Global Variables

| Variable | Type | Description |
|----------|------|-------------|
| `selectedNodes` | `{ name: string }[]` | List of injection target nodes currently selected by the user; each node contains only the `name` field |
| `currentInputMethod` | `string` | Current input mode: `json` or `file` |
| `uploadedFile` | `object \| null` | Stores the name and content of the uploaded file |

## Functions

### `setupEventListeners()`

Initializes page event bindings using an **event delegation** pattern to optimize dynamically generated node list interactions.

- **Search**: `#search-input` real-time filtering.
- **Validation**: `#json-textarea` real-time format validation.
- **Toggle**: `.input-toggle` switches input mode.
- **Selection**: `.button-group` handles select all/clear.
- **Submit**: `#submit-btn` triggers the injection flow.

---

### `renderNodeList(searchTerm)`

Renders the selectable node list based on `nodeStatuses`.

- **Status Filtering**: Nodes display corresponding status badges (Running/Stopped/Not Running).
- **Interaction Limitation**: Stopped nodes are set to `disabled-node` style and cannot be selected for injection.

---

### `handleSubmit()`

Executes the task injection submission logic.

1. **Get Data**: Retrieves textarea content or uploaded file content based on the current `currentInputMethod`.
2. **Data Validation**: Ensures selected nodes are not empty and data format is valid JSON (must be a list structure).
3. **Concurrent Injection**: Sends `POST /api/push_injection_tasks` requests separately for each selected node.
4. **Feedback Display**: Shows injection results on the page (success/failure/partial success).

---

### `switchInputMethod(method)`

Switches the UI between the JSON text area and file upload area.

---

### `handleFileUpload(e)`

Handles the file selection event, reads `.json` file content and calls `validateJSON()` for pre-validation.

---

### `fillTermination()`

Helper function: Fills the JSON input box with a standard task termination signal sequence in one click.

## Data Flow

```
1. Page interaction -> Select nodes + Input data
2. Click submit -> validateJSON() validation
3. Backend request -> POST /api/push_injection_tasks
4. UI feedback -> Display injection success/failure status
```

## Usage Example

### Task Injection Data Format and Usage

The following example shows the typical operation flow and data structure of the task injection feature:

```typescript
// 1. Simulate selected target nodes (containing only the name field)
const selectedNodes = [
    { name: "StageA" },
    { name: "StageB" },
];

// 2. Data format for task injection requests
// POST /api/push_injection_tasks
const injectionPayload = {
    node: "StageA",              // Target node label
    task_datas: [                // Task data list
        { id: 101, content: "file_a.csv" },
        { id: 102, content: "file_b.csv" },
        { id: 103, content: "file_c.csv" },
    ],
    timestamp: "2026-05-24T10:30:00",  // ISO format timestamp
};

// 3. Manually submit injection via fetch API
async function injectTasks(node: string, taskDatas: any[]) {
    const res = await fetch("/api/push_injection_tasks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            node,
            task_datas: taskDatas,
            timestamp: new Date().toISOString(),
        }),
    });
    return res.json();
}

// 4. Validate JSON data legality
function validateJSON(str: string): { valid: boolean; data?: any; error?: string } {
    try {
        const data = JSON.parse(str);
        if (!Array.isArray(data)) {
            return { valid: false, error: "Data must be a JSON array format" };
        }
        return { valid: true, data };
    } catch (e) {
        return { valid: false, error: "Invalid JSON format" };
    }
}

// 5. Use validateJSON to validate input
const validInput = '[{"id":1}, {"id":2}]';
const invalidInput = '{invalid json}';

console.log(validateJSON(validInput));
// { valid: true, data: [{ id: 1 }, { id: 2 }] }

console.log(validateJSON(invalidInput));
// { valid: false, error: "Invalid JSON format" }

// 6. Batch injection to multiple nodes
async function injectToMultipleNodes(nodes: string[], taskDatas: any[]) {
    const results = await Promise.allSettled(
        nodes.map(node => injectTasks(node, taskDatas))
    );
    
    const successCount = results.filter(r => r.status === "fulfilled").length;
    const failCount = results.filter(r => r.status === "rejected").length;
    
    console.log(`Injection complete: ${successCount} succeeded, ${failCount} failed`);
    return results;
}

// 7. Termination signal injection
// Fill the input box with termination signal via fillTermination()
const terminationPayload = ["TERMINATION_SIGNAL"];
// The backend stops processing tasks for the corresponding node upon receiving this signal
```
