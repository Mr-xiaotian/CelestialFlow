# demo_stages.py Demo Documentation

## Purpose

Demonstrates the usage of special Stage nodes in CelestialFlow: `TaskSplitter` (task splitting), `TaskRouter` (task routing), `TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource` (Redis distributed transport). Builds complex task graphs with cyclic dependencies and cross-device collaboration.

## Demo Scenarios

### `demo_splitter_0`
Simulates a web crawler workflow:
- `GenURLs` -> Generates a list of URLs
- `Logger` -> Logs crawling information
- `Splitter` -> Splits the URL list into individual URLs
- `Downloader` -> Downloads resources
- `Parser` -> Parses new URLs and loops back to `GenURLs`

**Graph structure**: Cyclic graph (`parse_stage -> generate_stage`)

### `demo_splitter_1`
Demonstrates large data packet splitting: input `range(int(1e5))` is wrapped in a list and passed to `TaskSplitter`, where downstream stages receive and process items individually, avoiding loading too many tasks into memory at once.

### `demo_redis_ack_0/1/2`
Compares the time difference between local Python computation and external computation via Redis + Go Worker:
- `demo_redis_ack_0`: Fibonacci (CPU-intensive)
- `demo_redis_ack_1`: `sum_int` (communication overhead dominant)
- `demo_redis_ack_2`: Image download (I/O-intensive)

### `demo_redis_source_0`
Demonstrates `TaskRedisSource` independently reading tasks from Redis, enabling cross-device/cross-TaskGraph data transport.

### `demo_router_0`
Demonstrates `TaskRouter` distributing tasks to different downstream nodes based on odd/even parity.

## Key Configuration

- All stages default to `stage_mode="process"` (multiprocessing)
- `set_reporter(True)` enables monitoring reporting
- `set_ctree(True)` enables event tracing

## Potential Issues

1. **Redis dependency**: The `demo_redis_*` series requires an available Redis service (`.env` configuration for `REDIS_HOST`, `REDIS_PASSWORD`).
2. **Go Worker prerequisite setup**: External Workers require completing the [prerequisite setup](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期设置) before use.
3. **Hardcoded network paths**: `DownloadStage` and `DownloadRedisTransport` contain hardcoded Windows paths (`X:/Download/...`) that will fail on non-Windows environments or when the paths don't exist.
4. **Long execution time**: Each stage in `demo_splitter_0` contains 4-6 seconds of random sleep; full execution may exceed 1 minute.
5. **No assertions**: Demo script; does not verify result correctness.

## How to Run

```bash
# Run a specific demo
python demo/demo_stages.py
```

## Dependencies

- `celestialflow` (`TaskGraph`, `TaskStage`, `TaskSplitter`, `TaskRouter`, `TaskRedisTransport`, `TaskRedisAck`, `TaskRedisSource`)
- `demo_utils`
- `python-dotenv`
- External services: Redis, CelestialTree (optional), Reporter (optional), Go Worker (optional)
