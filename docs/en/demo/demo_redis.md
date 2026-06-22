# demo_redis.py Demo Guide

> 📅 Last Updated: 2026/06/22

## Objective

Demonstrates how to implement Redis task submission, result acknowledgment, and external task injection using only ordinary `TaskStage` nodes and custom callables, without relying on built-in Redis-specific nodes.

## Design Highlights

- `redis_push(task)`: Serializes a task and writes it to a Redis List, returning `(key, task_id)`
- `redis_wait(task)`: Polls a Redis Hash, waiting for a remote Worker to write back the result
- `redis_pop(key)`: Uses `BLPOP` to block and pull a task from a Redis List
- All three capabilities are just ordinary Python methods, then attached to the graph via `TaskStage(..., func=helper)`

## Redis Interaction Flow

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        RSS[/RedisPushStage/]
        RPS[/RedisPopStage/]

        RE[(Redis)]

        RSS -.->|rpush task| RE -.->|blpop task| RPS

    end

    %% Style TaskGraph outer frame
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% Unified style
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% Style special Stages
    class RSS,RPS blueNode;

    %% Style external structures
    class RE blueNode;

```

**Note**: This Mermaid diagram is a favorite; do not delete.

## Core Helper Functions

### `redis_push`

Pushes a task to a Redis List.

```python
def redis_push(task: Any) -> int:
    """Push a task into Redis"""
    key, task_payload = task
    redis_client: redis.Redis = get_redis()
    task_id = next(_task_ids)
    payload = json.dumps(
        {
            "id": task_id,
            "task": [task_payload],
            "emit_ts": time.time(),
        }
    )
    _ = redis_client.rpush(f"{key}:input", payload)
    return key, task_id
```

**Behavior**: Splits `task` into `(key, payload)`, wraps it as JSON, and `rpush`es it to `{key}:input`. The actual return value is `(key, task_id)` for downstream `redis_wait` to use.

### `redis_pop`

Pulls a task from a Redis List as an input source.

```python
def redis_pop(key: str) -> Any:
    """Pop a task from Redis"""
    redis_client: redis.Redis = get_redis()
    res = cast(list[Any] | None, redis_client.blpop(key, timeout=redis_timeout))
    if res is None:
        raise CelestialFlowTimeoutError(
            "Redis item not returned in time after being fetched"
        )

    _, item = res
    item_obj = cast(dict[str, Any], json.loads(cast(str, item)))
    task_payload = item_obj.get("task")
    if task_payload is None:
        raise RemoteWorkerError("Redis source payload missing 'payload'")
    if len(task_payload) == 1:
        return task_payload[0]
    return tuple(task_payload)
```

**Behavior**: Uses `blpop` to block and pull tasks; throws `CelestialFlowTimeoutError` on timeout.

### `redis_wait`

```mermaid
flowchart LR
    subgraph TG[TaskRedis*]
        direction LR

        RPS[/RedisPushStage/]
        RWS[/RedisWaitStage/]

        RE[(Redis)]
        G1((GoWorker))
        G2((GoWorker))

        RPS -.->|task| RE -.->|task| G1
        G2 -.->|result| RE -.->|result| RWS

    end

    %% Style TaskGraph outer frame
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% Unified style
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% Style special Stages
    class RPS,RWS blueNode;

    %% Style external structures
    class RE,G1,G2 blueNode;

```

**Note**: This Mermaid diagram is a favorite; do not delete.

Waits for execution results from a remote Worker.

```python
def redis_wait(task: tuple[str, int]) -> Any:
    """Wait for task completion"""
    key, task_id = task
    redis_client: redis.Redis = get_redis()
    start_time = time.perf_counter()

    while True:
        result = cast(str | None, redis_client.hget(f"{key}:output", str(task_id)))
        if result:
            _ = redis_client.hdel(f"{key}:output", str(task_id))
            result_obj = cast(dict[str, Any], json.loads(result))
            status = result_obj.get("status")
            if status == "success":
                return _normalize_result(result_obj.get("result"))
            if status == "error":
                raise RemoteWorkerError(str(result_obj.get("error")))
            raise RemoteWorkerError(f"Unknown ack status: {result_obj}")

        if (time.perf_counter() - start_time) > redis_timeout:
            raise CelestialFlowTimeoutError(
                f"Redis ack timeout: task_id={task_id} not acknowledged"
            )
        time.sleep(0.1)
```

**Behavior**: Polls Redis Hash `{key}:output` waiting for the result corresponding to `task_id`. Supports handling success results or raising `RemoteWorkerError`.

## Redis Data Format

### Transport Push Format

The JSON structure written to the Redis List by `redis_push()` is as follows:

```json
{
  "id": 123,
  "task": ["payload"],
  "emit_ts": 1703001234.567
}
```

Field descriptions:

- `id`: Locally generated task number
- `task`: Task payload, uniformly packaged as a list
- `emit_ts`: Send timestamp, useful for debugging and latency investigation

### Ack Expected Result Format

When the remote Worker writes back to the Redis Hash, a success result should look like:

```json
{
  "status": "success",
  "result": "computed_value"
}
```

An error result should look like:

```json
{
  "status": "error",
  "error": "Error message"
}
```

### Source Read Format

The Redis List elements read by `redis_pop()` also follow the same payload structure as Transport, meaning they must contain at least:

```json
{
  "task": ["payload"]
}
```

## Demo Scenarios

### `demo_redis_ack_0/1/2`

Compares the two paths of "local Python direct execution" and "sending to an external Worker via Redis".

```mermaid
flowchart TB
    Start["Start<br/>sleep_1_*"] --> Local["Local compute Stage<br/>Fibonacci / Sum / Download"]
    Start --> Transport["TaskStage(RedisTransport)<br/>redis_push"]
    Transport -.-> RedisIn[(Redis input list)]
    RedisOut[(Redis output hash)] -.-> Ack["TaskStage(RedisAck)<br/>redis_wait"]
```

| Scenario | Local Node | Remote Input Key | Remote Output Key |
|------|----------|--------------|--------------|
| `demo_redis_ack_0` | `Fibonacci` | `testFibonacci:input` | `testFibonacci:output` |
| `demo_redis_ack_1` | `Sum` | `testSum:input` | `testSum:output` |
| `demo_redis_ack_2` | `Download` | `testDownload:input` | `testDownload:output` |

The three scenarios differ only in the local direct-computation stage:

- `demo_redis_ack_0`: CPU-intensive Fibonacci
- `demo_redis_ack_1`: Lightweight summation
- `demo_redis_ack_2`: Real download I/O

They share the same pattern:

- The `Start` node produces `(key, payload)` tuples
- One path goes directly into the local compute stage
- One path goes into `RedisTransport`, where `redis_push` writes to Redis
- The `(key, task_id)` output by `RedisTransport` goes into `RedisAck`
- `RedisAck` waits for the remote Worker to write back the result via `redis_wait`

### `demo_redis_source_0`

Demonstrates how to use Redis as an external input source to the graph: one stage writes to it, and another stage pulls via `BLPOP` and continues downstream processing.

```mermaid
flowchart LR
    Sleep0["Sleep0<br/>sleep_1_report"] --> Transport["TaskStage(RedisTransport)<br/>redis_push"]
    Transport -.-> Redis[(Redis list)]
    Redis -.-> Source["TaskStage(RedisSource)<br/>redis_pop"]
    Source --> Sleep1["Sleep1<br/>sleep_1"]
```

This scenario emphasizes "Redis as an inter-graph bridge input source":

- `Sleep0` first writes tasks into Redis
- `RedisSource` then independently fetches tasks from Redis
- `Sleep1` receives the Redis-injected tasks and continues processing

## Prerequisites

### 1. Start Redis

Before running this demo, ensure the Redis service is available.

### 2. Configure Environment Variables

The `.env` file in the project root should contain at least:

```env
REDIS_HOST=127.0.0.1
REDIS_PASSWORD=
REPORT_HOST=127.0.0.1
REPORT_PORT=8000
```

### 3. Prepare Remote Workers (only needed for Ack scenarios)

To actually observe remote result write-back in `demo_redis_ack_*`, you need an external Worker that:

- Pulls tasks from the corresponding input list
- Executes them according to the agreed structure
- Writes results back to the corresponding output hash

For details on the remote `go-worker` project, see [other/go_worker.md](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/zh-CN/other/go_worker.md)

## How to Run

```bash
# Run the default example (demo_redis_source_0)
python demo/demo_redis.py

# For Ack scenarios, modify the entry function in main at the bottom of the file
```

You can also directly open [demo_redis.py](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/demo/demo_redis.py) and switch the final `if __name__ == "__main__":` entry.

## Potential Issues

1. **Default entry switched**: The current `__main__` defaults to running `demo_redis_source_0`, not the older `demo_redis_ack_0`.
2. **Timeout**: If the external Worker does not write back in time, `redis_wait()` throws `CelestialFlowTimeoutError`.
3. **Protocol mismatch**: If the Worker-written JSON lacks `status` or `result/error` fields, `RemoteWorkerError` is thrown.
4. **Network and path dependencies**: `demo_redis_ack_2` involves real download URLs and local paths `X:/Download/download_py/...`, which may fail depending on the environment.
5. **No assertions**: This is an integration demo; it does not validate business result correctness.
6. **Local `task_id` scope**: `redis_push`'s `task_id` is an incrementing value within the current process, suitable for demos and single-end collaboration, but not equivalent to a globally distributed unique ID.
7. **Single consumption**: `redis_wait` immediately calls `HDEL` after retrieving a result, so the same result is not read twice by default.

## Notes

1. **Connection management**: The Redis client is lazily initialized on first use and reused throughout the helper's lifecycle.
2. **Timeout handling**: Both `redis_pop` and `redis_wait` use the module-level `redis_timeout` (default 5 seconds).
3. **Error propagation**: Errors returned by remote Workers are directly thrown upward via `RemoteWorkerError`.
4. **Replaceable protocol**: You can fully modify the JSON structure to match your own Worker protocol, as long as you synchronize the three helpers.
5. **Framework positioning**: What is shown here is "how to implement Redis integration using ordinary `TaskStage`", not a requirement for the framework to have built-in Redis nodes.

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`)
- `celestialflow.runtime.util_errors` (`CelestialFlowTimeoutError`, `RemoteWorkerError`)
- `demo_utils`
- `python-dotenv`
- `redis`
- `requests` (for `demo_redis_ack_2` downloads)
- External services: Redis, remote Worker (optional), Reporter (optional)
