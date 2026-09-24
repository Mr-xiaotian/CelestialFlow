# src/celestialflow/persistence/core_lifecycle.py

> 📅 Last Updated: 2026/09/24

`persistence/core_lifecycle.py` handles task lifecycle persistence: it records task state transitions throughout the lifecycle (pending → success / failed, and retry count updates), and writes the data into SQLite database files under the `lifecycles/` directory. The core components are `LifecycleSpout` and `LifecycleInlet`.

## Architecture

### Data Flow

```mermaid
flowchart LR
    subgraph Producer["Producer - Worker Thread"]
        Inlet[LifecycleInlet]
        Inlet -->|task_input / task_success / task_fail etc.| Funnel[_funnel]
    end
    Funnel --> Queue[queue.Queue]
    Queue -->|Daemon thread polling| Spout[LifecycleSpout._handle_record]
    Spout -->|Ops: insert / promote / update_retry| SQLite[lifecycles/**/*.sqlite3]
    SQLite --> Read[get_task_error_pairs<br/>get_task_result_pairs<br/>Read persisted records]
```

The system follows a **Producer-Consumer** pattern:

1.  **LifecycleInlet (Producer)**: held by individual executors; responsible for wrapping task lifecycle events into operation dictionaries and placing them into a thread-safe queue.
2.  **LifecycleSpout (Consumer)**: runs in a dedicated daemon thread, continuously monitoring the queue and performing the corresponding SQLite write operations according to the operation type (`__op__`).

## LifecycleSpout

`LifecycleSpout` inherits from `BaseSpout` and is responsible for managing the creation and writing of SQLite database files.

### Initialization and Startup

```python
class LifecycleSpout(BaseSpout):
    def __init__(self) -> None:
        """Initialize the lifecycle record listener."""
```

After startup (`_before_start()`), a `flow_lifecycle({time}).sqlite3` file is created under the `./lifecycles/{date}/` directory and a sqlite connection is established:

```python
from celestialflow.persistence import LifecycleSpout

lifecycle_spout = LifecycleSpout()
lifecycle_spout.start()
```

`_after_stop()` calls `commit()` first and then closes the connection, ensuring remaining transactions are flushed to disk.

### _handle_record Operation Types

`LifecycleSpout._handle_record` executes different SQLite operations based on `record["__op__"]`:

| Operation | Triggered By | Description |
|-----------|--------------|-------------|
| `insert` | `LifecycleInlet.task_input()` | A new task enters a stage; writes a `pending` record |
| `promote_success` | `LifecycleInlet.task_success()` | Promotes the pending record to `success`; writes the result JSON |
| `promote_failed` | `LifecycleInlet.task_fail()` | Promotes the pending record to `failed`; updates event_id and writes the error type and message |
| `update_retry` | `LifecycleInlet.task_retry()` | Keeps the `pending` state, only updates `retry_times` and the error type / message of the most recent failure |

Each operation calls `commit()` immediately after the record is actually modified; an unknown `__op__` raises a `ValueError`.

### File Path

Lifecycle data is saved under `./lifecycles/` by default, archived by date:

```text
./lifecycles/
└── 2026-08-26/
    └── flow_lifecycle(14-30-05-123).sqlite3
```

### Reading Persisted Records

```python
# Get error records
error_pairs: list[tuple[Any, tuple[str, str]]] = lifecycle_spout.get_task_error_pairs(
    "StageA"
)
# Returns [(task, (error_type, error_message)), ...]

# Get success results
result_pairs: list[tuple[Any, Any]] = lifecycle_spout.get_task_result_pairs("StageA")
# Returns [(task, result), ...]
```

Both methods return an empty list when `db_path` has not yet been initialized.

## LifecycleInlet

`LifecycleInlet` inherits from `BaseInlet` and is a thread-safe write wrapper for the lifecycle queue.

### Core Methods

```python
class LifecycleInlet(BaseInlet):
    def task_input(self, stage_name: str, event_id: int, task: Any) -> None:
        """写入一条 pending 记录，表示任务已进入某个 stage。"""

    def task_success(self, event_id: int, result: Any) -> None:
        """将 pending 记录晋升为 success 并写入结果。"""

    def task_fail(self, event_id: int, error_id: int, error: Exception) -> None:
        """将 pending 晋升为 failed，绑定最终错误信息。"""

    def task_retry(self, event_id: int, retry_times: int, error: Exception) -> None:
        """更新 pending 记录的重试次数与最近一次失败的错误信息。"""
```

Notes:

- In `task_input`, `task` is serialized via `to_persisted_payload()` into a JSON-friendly structure and stored in the `task_json` field.
- `task_fail` persists `error_type` (exception class name) together with `error_message` (`str(error)`).
- `task_retry` only updates `retry_times` and the most recent error information; the record stays in the `pending` state, and is ultimately promoted by `task_success` / `task_fail`.
- `LifecycleInlet` only writes to the queue and does not directly operate on the database; all I/O is performed in the background thread of `LifecycleSpout`.

## Global Singletons

```python
get_lifecycle_spout() -> LifecycleSpout  # The globally unique LifecycleSpout instance
get_lifecycle_inlet() -> LifecycleInlet  # The globally unique LifecycleInlet instance (already bound to the global spout)
```

The framework's execution components (`BaseTaskNode` / `TaskSplitter` / `TaskRouter` / `TaskGraph`) uniformly use `get_lifecycle_inlet()` to record lifecycle events, while `BaseTaskNode.get_success_pairs()` and `get_error_pairs()` read results through `get_lifecycle_spout()`.

## Usage Examples

### Lifecycle Operations

```python
from celestialflow.persistence import LifecycleInlet, LifecycleSpout

# 1. Create and start LifecycleSpout
lifecycle_spout = LifecycleSpout()
lifecycle_spout.start()

# 2. Create LifecycleInlet and bind it
lifecycle_inlet = LifecycleInlet().bind_spout(lifecycle_spout)

# 3. 记录任务生命周期
lifecycle_inlet.task_input("StageA", event_id=1, task="hello")

# 任务成功：pending -> success
lifecycle_inlet.task_success(event_id=1, result="OK")

# 任务失败：pending -> failed
lifecycle_inlet.task_fail(event_id=2, error_id=10, error=ValueError("bad input"))

# 任务重试：更新 pending 记录的重试次数（状态仍为 pending）
lifecycle_inlet.task_retry(event_id=2, retry_times=1, error=ValueError("bad input"))

# 4. 获取持久化数据
errors = lifecycle_spout.get_task_error_pairs("StageA")
for task, (error_type, error_msg) in errors:
    print(f"失败任务: {task}, 错误: {error_type}: {error_msg}")

# 5. Stop
lifecycle_spout.stop()
```

In actual usage, you usually obtain the global singletons through `get_lifecycle_inlet()` / `get_lifecycle_spout()` without manually creating them.

## Notes

1. **SQLite storage**: uses WAL mode + `check_same_thread=False`, supporting cross-thread read/write (see `util_sqlite.connect_db`).
2. **Immediate commit**: each write operation commits immediately after the record is actually modified, ensuring no data is lost.
3. **Inlet only writes the queue**: it does not directly operate on the database; all I/O is performed in the background thread of `LifecycleSpout`.
