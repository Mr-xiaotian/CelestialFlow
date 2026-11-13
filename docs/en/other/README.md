# Other Module

> 📅 Last Updated: 2026/11/13

## Overview

The Other module contains extension components and external integrations of the CelestialFlow framework. These components are not part of the core framework but provide important extension capabilities. It mainly includes two components: the CelestialTree client and the Go Worker, which are used for task provenance tracing and cross-language task execution respectively.

## File Details

### 1. ctree_client.md - CelestialTree Client

**Purpose**: Integrate the CelestialTree event-sourcing system to achieve full-chain task tracing and event recording.

**Core features**:
- **Event recording**: Automatically records key events in the task lifecycle (input, success, failure, retry, termination merge, etc.)
- **Data lineage tracing**: Queries the data sources and generation paths of results
- **Error root cause localization**: Traces the complete call chain of failed tasks
- **Execution tree visualization**: Generates the call tree structure of task execution

**Key characteristics**:
- Integrates with the CelestialTree service, supporting HTTP and gRPC communication
- Automatic event emission, no manual instrumentation required
- Provides simplified provenance query interfaces
- Supports complex scenarios such as task splitting and routing

**Usage pattern**:
```python
from celestialtree import Client as CelestialTreeClient

# After installing celestialtree separately, construct and inject the client
ctree_client = CelestialTreeClient(
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
)

graph.set_ctree(ctree_client)
```

### 2. go_worker.md - Go Worker Task Consumer

**Purpose**: A lightweight, concurrency-scalable Redis-based task consumer (Worker Pool) for cross-language task execution.

**Core features**:
- **Task consumption**: Continuously consumes tasks from a Redis queue
- **Concurrent execution**: Executes tasks with controllable concurrency
- **Result write-back**: Writes execution results back to Redis
- **Cross-language support**: Serves as a Go execution node of TaskGraph

**Architectural characteristics**:
- **Worker Pool pattern**: Uses goroutines and channels for concurrency control
- **Automatic reconnection**: Supports exponential backoff retries when Redis connections fail
- **Pluggable design**: Parser and Processor can be customized and extended
- **Generic task structure**: Uses JSON-format task payloads

**Key components**:
- **TaskParser**: Parses task payloads and converts them into the format required by Processor
- **TaskProcessor**: Executes business logic and returns computation results
- **Worker Pool**: Manages concurrent execution and resource control

**Usage pattern**:
```go
// Start the Worker Pool
worker.StartWorkerPool(
    ctx,
    rdb,
    "testFibonacci:input",  // Redis input queue
    "testFibonacci:output", // Redis output hash
    worker.ParseListTask,   // Task parser
    worker.Fibonacci,       // Task processor
    4,                      // Concurrency
)
```

## Module Relationships

### Relationship with the Core Framework

1. **CelestialTree client**:
   - Tightly integrated with `TaskGraph`, automatically recording task events
   - Depends on the event emission mechanism of the `observer` module (`Event` subclasses are dispatched via `ObserverHub.on_event()`)
   - Provides provenance data support for the `web` module

2. **Go Worker**:
   - Works with helpers such as `redis_push()` / `redis_wait()` in `demo/demo_redis.py`
   - Communicates with the Python-side `TaskGraph` via Redis
   - Can be used as a standalone component without a hard dependency on the core framework

### Inter-Component Collaboration

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **Task execution flow**:
   - TaskGraph generates tasks and writes them to Redis
   - Go Worker consumes tasks from Redis and executes them
   - Execution results are written back to Redis, and TaskGraph reads the results
   - The CelestialTree client records events for the whole flow

2. **Data flow**:
   - Task data is passed between Python and Go via Redis
   - Event data is sent to CelestialTree via HTTP/gRPC
   - Provenance queries are fetched from CelestialTree via the client API

## Architectural Characteristics

### 1. Loosely Coupled Design
- Each component can be deployed and used independently
- Communicates via standard protocols (Redis, HTTP)
- No language binding; supports multi-language extension

### 2. Enhanced Observability
- CelestialTree provides fine-grained task provenance
- Supports error tracing and performance analysis
- Complements the framework's monitoring metrics

### 3. Performance Optimization
- Go Worker provides high-performance task execution
- Concurrency control avoids resource exhaustion
- Automatic reconnection ensures system stability

## Usage Patterns

### 1. Full-Chain Tracing Mode
```python
# First construct the CelestialTree client, then enable tracing
graph.set_ctree(ctree_client)

# Run the task graph
graph.run(init_tasks)
```

### 2. Cross-Language Execution Mode
```python
# Python side: wrap the demo_redis helpers with ordinary TaskExecutor
transport_node = TaskExecutor("RedisTransport", redis_push)
ack_node = TaskExecutor("RedisAck", redis_wait)

# Go side: start a Worker Pool to consume tasks
# Configure the same Redis keys in go_worker/main.go
```

### 3. Hybrid Mode
Use CelestialTree tracing and Go Worker execution at the same time to obtain complete observability and high-performance execution.

## Best Practices

### 1. CelestialTree Configuration
- Deploy an independent CelestialTree service in production
- Adjust the event sampling rate according to task volume
- Periodically clean up expired event data

### 2. Go Worker Deployment
- Choose an appropriate concurrency level based on task types
- Monitor Redis connection status and queue length
- Implement custom Processors to handle specific business logic

### 3. Error Handling
- Add comprehensive error logging to the Go Worker
- Implement task retry and dead-letter queue mechanisms
- Monitor CelestialTree connection status

### 4. Performance Tuning
- Adjust the Redis connection pool size
- Optimize the serialization format of task payloads
- Adjust Worker concurrency based on hardware resources

## Extension Suggestions

### 1. Adding Processors
Add new Processor functions in `go_worker/worker/processors.go` to support more task types.

### 2. Custom Parsers
Implement custom TaskParsers to support parsing complex task formats.

### 3. Monitoring Integration
Integrate Go Worker metrics into the framework's monitoring system for unified observability.

### 4. Multi-Language Support
Refer to the Go Worker pattern to implement Worker components in other languages (e.g., Java, Rust).

## Notes

1. **Version compatibility**: Ensure that the CelestialTree client and server versions are compatible
2. **Network latency**: Network latency between Redis and CelestialTree affects overall performance
3. **Resource management**: Configure Worker concurrency reasonably to avoid resource contention
4. **Data consistency**: Pay attention to the use of Redis transactions and atomic operations
5. **Security considerations**: Protect the access credentials of Redis and CelestialTree
