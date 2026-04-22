# TaskNodes

The TaskNodes module provides multiple specialized `TaskStage` implementations for flow control, external system interaction, and other scenarios.

## TaskSplitter

```mermaid
flowchart LR
    subgraph TG[TaskSplitter]
        direction LR

        T1[Last Stage]
        T2[Next Stage]

        TS[[TaskSplitter]]

        T1 -->|1 task| TS
        TS -->|N task| T2

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2 blueNode;

    %% 美化 特殊Stage
    class TS blueNode;

```

Splits a single input task into multiple output tasks. Suitable for one-to-many scenarios.

### Initialization

```python
class TaskSplitter(TaskStage):
    def __init__(self):
        """
        Initialize TaskSplitter.
        Defaults: execution_mode="serial", max_retries=0, unpack_task_args=True
        """
```

### Usage

```python
class MySplitter(TaskSplitter):
    def _split(self, *task):
        # Split input data into multiple parts
        return task[0], task[1]  # Returns a tuple; each element becomes an independent task
```

### Features

- **Mechanism**: Takes a single task as input and returns a tuple/list. Each element is wrapped into an independent `TaskEnvelope` and sent downstream.
- **Counting**: Internally maintains a `split_counter` to track the total number of split tasks.
- **Default Configuration**: `execution_mode="serial"`, `max_retries=0`, `unpack_task_args=True`

---

## TaskRouter

```mermaid
flowchart LR
    subgraph TG[TaskRouter]
        direction LR

        T1[Last Stage]
        T2[Next Stage 1]
        T3[Next Stage 2]

        TR{{TaskRouter}}

        T1 -->|2 task| TR
        TR -->|1 task| T2
        TR -->|1 task| T3

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2,T3 blueNode;

    %% 美化 特殊Stage
    class TR blueNode;

```

Routes tasks to different downstream paths based on conditions.

### Initialization

```python
class TaskRouter(TaskStage):
    def __init__(self):
        """
        Initialize TaskRouter.
        Defaults: execution_mode="serial", max_retries=0
        """
```

### Usage

Routing tasks requires returning a tuple in the `(target_tag, data)` format:

```python
# Define upstream task to generate routing tuples
def route_logic(data):
    if data > 0:
        return ("positive_stage", data)
    else:
        return ("negative_stage", data)

# Create a router node
router = TaskRouter()

# Connect downstream (target must match the tag in the routing logic)
graph.connect([router], [pos_stage, neg_stage])
```

### Features

- **Mechanism**: Receives tuples in the `(target_tag, data)` format. Sends `data` to the corresponding downstream Stage based on `target_tag`.
- **Counting**: Maintains independent counters `route_counters` for each target.
- **Error Handling**: Raises `InvalidOptionError` if the `target_tag` does not exist in the downstream list.

---

## Redis Integration

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        TRSI[/TaskRedisTransport/]
        TRSO[/TaskRedisSource/]

        RE[(Redis)]

        TRSI -.-> RE -.->  TRSO

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class TRSI,TRSO blueNode;

    %% 美化 外部结构
    class RE blueNode;

```

Provides nodes for interacting with Redis, commonly used for cross-language/cross-process collaboration (e.g., with Go Workers).

### TaskRedisTransport

Pushes tasks to a Redis List.

```python
class TaskRedisTransport(TaskStage):
    def __init__(
        self,
        key: str,                       # Redis List name
        host: str = "localhost",        # Redis host address
        port: int = 6379,               # Redis port
        db: int = 0,                    # Redis database number
        password: str | None = None,    # Redis password
        unpack_task_args: bool = False, # Whether to unpack task arguments
    ):
        ...
```

**Behavior**: Serializes tasks to JSON and `rpush`es them to a Redis List. Internally uses `execution_mode="thread"` and `max_workers=4` for concurrent writes.

### TaskRedisSource

Pulls tasks from a Redis List as an input source.

```python
class TaskRedisSource(TaskStage):
    def __init__(
        self,
        key: str,                    # Redis List name
        host: str = "localhost",     # Redis host address
        port: int = 6379,            # Redis port
        db: int = 0,                 # Redis database number
        password: str | None = None, # Redis password
        timeout: int = 10,           # Blocking timeout in seconds; 0 means wait indefinitely
    ):
        ...
```

**Behavior**: Uses `blpop` for blocking task retrieval. Internally uses `execution_mode="serial"`, suitable as a pipeline entry node.

### TaskRedisAck

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        TRSI[/TaskRedisTransport/]
        TRA[/TaskRedisAck/]

        RE[(Redis)]
        G1((GoWorker))
        G2((GoWorker))

        TRSI -.->|task| RE -.->|task| G1
        G2 -.->|result| RE -.->|result| TRA

    end

    %% 美化 TaskGraph 外框
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 统一美化格式
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 特殊Stage
    class TRSI,TRA blueNode;

    %% 美化 外部结构
    class RE,G1,G2 blueNode;

```

Waits for execution results from remote Workers.

```python
class TaskRedisAck(TaskStage):
    def __init__(
        self,
        key: str,                    # Redis Hash name (stores results)
        host: str = "localhost",     # Redis host address
        port: int = 6379,            # Redis port
        db: int = 0,                 # Redis database number
        password: str | None = None, # Redis password
        timeout: int = 10,           # Wait timeout in seconds; 0 means wait indefinitely
    ):
        ...
```

**Behavior**: Polls a Redis Hash waiting for the corresponding `task_id` result. Supports handling successful results or raising `RemoteWorkerError`.

---

## Prerequisites

### 1. Start the Redis Service

Before running `TaskRedis*` nodes, you need to start the Redis service.

### 2. Set Environment Variables (Optional)

Create a `.env` file in the project root directory:

```env
# .env
# Redis service address
REDIS_HOST=127.0.0.1
# Redis service port
REDIS_PORT=6379
# Redis service password; leave empty if none
REDIS_PASSWORD=your_redis_password
```

### 3. Configure Nodes

```python
import os
from dotenv import load_dotenv
from celestialflow import TaskRedisTransport, TaskRedisAck, TaskRedisSource

# Load environment variables
load_dotenv()

redis_host = os.getenv("REDIS_HOST", "127.0.0.1")
redis_password = os.getenv("REDIS_PASSWORD", "")

# Transport + Ack combination (push to Redis and wait for results)
redis_sink = TaskRedisTransport(
    key="testFibonacci:input",
    host=redis_host,
    password=redis_password
)
redis_ack = TaskRedisAck(
    key="testFibonacci:output",
    host=redis_host,
    password=redis_password
)

# Source combination (pull tasks from Redis)
redis_source = TaskRedisSource(
    key="test_redis",
    host=redis_host,
    password=redis_password
)
```

---

## Redis Data Format

### TaskRedisTransport Push Format

```json
{
    "id": 12345678,
    "task": ["arg1", "arg2"],
    "emit_ts": 1703001234.567
}
```

### TaskRedisAck Expected Result Format

```json
{
    "status": "success",
    "result": "computed_value"
}
```

Or error format:
```json
{
    "status": "error",
    "error": "Error message"
}
```

---

## Notes

1. **Connection Management**: The Redis client is lazily initialized on first use.
2. **Timeout Handling**: `TaskRedisSource` and `TaskRedisAck` support timeout configuration; timeouts raise `TimeoutError`.
3. **Error Propagation**: Errors returned by remote Workers are propagated via `RemoteWorkerError`.
4. **Idempotency**: `TaskRedisAck` deletes the record from Redis after retrieving the result, ensuring one-time consumption.
