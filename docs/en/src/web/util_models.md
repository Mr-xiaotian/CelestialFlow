# util_models

> 📅 Last Updated: 2026/06/05

## Purpose

The `celestialflow.web.util_models` module defines all Pydantic data models used by the Web module for data validation, serialization, and API request/response type constraints.

## Model List

### StructureModel

Task structure data model, representing the structure information of the task graph.

| Field | Type | Description |
|-------|------|-------------|
| `structure` | `dict[str, Any]` | Structure snapshot dictionary, typically containing `nodes`, `edges`, `source_nodes` |

### StatusModel

Node status data model, representing the running status of each node.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `float` | Timestamp of the status data (Unix) |
| `status` | `dict[str, dict[str, Any]]` | Mapping from node name to status dictionary |

### ErrorsMetaModel

Error metadata model, representing meta information of the error log file.

| Field | Type | Description |
|-------|------|-------------|
| `jsonl_path` | `str` | Error log JSONL file path |
| `rev` | `int` | Current revision/offset of the error log |

### ErrorsContentModel

Error content data model, containing the complete list of error records.

| Field | Type | Description |
|-------|------|-------------|
| `errors` | `list[dict[str, Any]]` | List of error records, each item is an error dictionary |
| `jsonl_path` | `str` | Error log JSONL file path |
| `rev` | `int` | Current revision/offset of the error log |

### AnalysisModel

Task analysis data model.

| Field | Type | Description |
|-------|------|-------------|
| `analysis` | `dict[str, Any]` | Analysis result dictionary |

### TaskInjectionModel

Task injection request model, used to dynamically insert new tasks into a running task graph.

| Field | Type | Description |
|-------|------|-------------|
| `node` | `str` | Injection target node name |
| `task_datas` | `list[Any]` | List of task data to inject; backend requires it to be an array |
| `timestamp` | `datetime` | Injection request timestamp |

### DashboardConfigModel

Dashboard layout configuration model, defining the frontend panel card layout.

| Field | Type | Description |
|-------|------|-------------|
| `left` | `list[str]` | List of card types to display in the left panel |
| `middle` | `list[str]` | List of card types to display in the middle panel |
| `right` | `list[str]` | List of card types to display in the right panel |

### WebConfigModel

Web UI global configuration model.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `theme` | `str` | — | UI theme |
| `autoRefreshEnabled` | `bool` | `True` | Whether auto-refresh is enabled |
| `refreshInterval` | `int` | — | Page data refresh interval (ms) |
| `historyLimit` | `int` | — | History record count limit |
| `language` | `str` | `"zh-CN"` | Interface language |
| `errorPageSize` | `int` | `10` | Error page items per page |
| `errorSortOrder` | `str` | `"newest"` | Error page sort order |
| `showStructureEdgeDelta` | `bool` | `True` | Whether to show structure diagram edge deltas |
| `dashboard` | `DashboardConfigModel` | — | Dashboard layout configuration (nested model) |

## Usage Examples

### Data Validation and Serialization

```python
from celestialflow.web.util_models import WebConfigModel, DashboardConfigModel, TaskInjectionModel

# --- WebConfigModel usage ---
config = WebConfigModel(
    theme="dark",
    autoRefreshEnabled=True,
    refreshInterval=5,
    historyLimit=20,
    language="zh-CN",
    errorPageSize=10,
    errorSortOrder="newest",
    showStructureEdgeDelta=True,
    dashboard=DashboardConfigModel(
        left=["mermaid"],
        middle=["status"],
        right=["progress"],
    ),
)
print(f"Theme: {config.theme}")
print(f"Dashboard layout: {config.dashboard.model_dump()}")

# Serialize to dict
config_dict = config.model_dump()

# Create from dict
restored = WebConfigModel(**config_dict)

# --- TaskInjectionModel usage ---
from datetime import datetime

injection = TaskInjectionModel(
    node="StageA",
    task_datas=[{"id": 1, "value": 42}, {"id": 2, "value": 99}],
    timestamp=datetime.now(),
)
print(f"Injection target: {injection.node}, task count: {len(injection.task_datas)}")
```

> Note: `TaskInjectionModel.task_datas` is currently strictly `list[Any]`. If the frontend uploads a single object, string, or number, wrap it in an array first; otherwise the endpoint will return 422.

### Error Data Processing

```python
from celestialflow.web.util_models import ErrorsContentModel, ErrorsMetaModel

# Error metadata
meta = ErrorsMetaModel(jsonl_path="./fallback/2026-05-28/errors.jsonl", rev=150)
print(f"Error log path: {meta.jsonl_path}, current offset: {meta.rev}")

# Error content
errors = ErrorsContentModel(
    errors=[
        {"error_type": "ValueError", "error_message": "Invalid input"},
        {"error_type": "TimeoutError", "error_message": "Connection lost"},
    ],
    jsonl_path="./fallback/2026-05-28/errors.jsonl",
    rev=152,
)
print(f"Error count: {len(errors.errors)}")
```
