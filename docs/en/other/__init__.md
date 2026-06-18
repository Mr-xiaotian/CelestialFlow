# Other Module

> 📅 Last Updated: 2026/06/18

## Overview

The Other module contains extension components and external integrations for the CelestialFlow framework. These components are not part of the core framework but provide important extended functionality. It primarily includes the CelestialTree client and Go Worker, used for task provenance tracing and cross-language task execution respectively.

## Detailed File Descriptions

### 1. ctree_client.md - CelestialTree Client

**Purpose**: Integrates the CelestialTree event provenance system to enable full-chain task tracing and event recording.

**Core Features**:
- **Event Recording**: Automatically records key events in the task lifecycle (input, success, failure, retry, split, route, etc.)
- **Data Lineage Tracing**: Query the data source and generation path of results
- **Root Cause Localization**: Trace the complete call chain of failed tasks
- **Execution Tree Visualization**: Generate the call tree structure of task execution

**Key Characteristics**:
- Integrates with the CelestialTree service, supporting HTTP and gRPC communication
- Automatic event emission, no manual instrumentation required
- Provides simplified provenance query interfaces
- Supports complex scenarios such as task splitting, routing, and duplicate detection

**Usage Pattern**:
```python
from celestialtree import Client as CelestialTreeClient

# After separately installing celestialtree, construct and inject the client
ctree_client = CelestialTreeClient(
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778,
)

graph.set_ctree(ctree_client)

# Query provenance information
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
error_trace = graph.get_error_trace(error_id=12345)
```

### 2. go_worker.md - Go Worker Task Consumer

**Purpose**: A lightweight, concurrently scalable, Redis-based task consumer (Worker Pool) for cross-language task execution.

**Core Features**:
- **Task Consumption**: Continuously consumes tasks from Redis queues
- **Concurrent Execution**: Executes tasks with controllable concurrency
- **Result Write-back**: Writes execution results back to Redis
- **Cross-Language Support**: Serves as a Go-language execution node for TaskGraph

**Architectural Characteristics**:
- **Worker Pool Pattern**: Uses goroutines and channels for concurrency control
- **Auto-Reconnect Mechanism**: Supports exponential backoff retry on Redis connection failures
- **Pluggable Design**: Parser and Processor are customizable and extensible
- **Generic Task Structure**: Uses JSON-formatted task payloads

**Key Components**:
- **TaskParser**: Parses task payloads, converting them to the format required by the Processor
- **TaskProcessor**: Executes business logic and returns computation results
- **Worker Pool**: Manages concurrent execution and resource control

**Usage Pattern**:
```go
// Start Worker Pool
worker.StartWorkerPool(
    ctx,
    rdb,
    "testFibonacci:input",  // Redis input queue
    "testFibonacci:output", // Redis output hash
    worker.ParseListTask,   // Task parser
    worker.Fibonacci,       // Task processor
    4,                      // Concurrency level
)
```

## Module Relationships

### Relationship with Core Framework

1. **CelestialTree Client**:
   - Tightly integrated with `TaskGraph`, automatically recording task events
   - Depends on the event emission mechanism of the `observability` module
   - Provides provenance data support for the `web` module

2. **Go Worker**:
   - Works with `redis_push()` / `redis_wait()` and similar helpers in `demo/demo_redis.py`
   - Communicates with the Python-side `TaskGraph` via Redis
   - Can be used as a standalone component without mandatory dependency on the core framework

### Inter-Component Collaboration

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **Task Execution Flow**:
   - TaskGraph generates tasks and writes them to Redis
   - Go Worker consumes tasks from Redis and executes them
   - Execution results are written back to Redis, and TaskGraph reads the results
   - CelestialTree client records events throughout the entire process

2. **Data Flow**:
   - Task data is passed between Python and Go via Redis
   - Event data is sent to CelestialTree via HTTP/gRPC
   - Provenance queries are obtained from CelestialTree through the client API

## Architectural Characteristics

### 1. Loose Coupling Design
- Each component can be deployed and used independently
- Communication via standard protocols (Redis, HTTP)
- No language binding, supporting multi-language extensions

### 2. Enhanced Observability
- CelestialTree provides fine-grained task provenance
- Supports error tracking and performance analysis
- Complements the framework's monitoring metrics

### 3. Performance Optimization
- Go Worker provides high-performance task execution
- Concurrency control prevents resource exhaustion
- Auto-reconnect ensures system stability

## Usage Patterns

### 1. Full-Chain Tracing Pattern
```python
# First construct a CelestialTree client, then enable tracing
graph.set_ctree(ctree_client)

# Run the task graph
graph.start_graph(init_tasks)

# Query task provenance
trace = graph.get_stage_input_trace("ProcessingStage")
```

### 2. Cross-Language Execution Pattern
```python
# Python side: encapsulate demo_redis helpers using ordinary TaskStage
transport_stage = TaskStage("RedisTransport", redis_push)
ack_stage = TaskStage("RedisAck", redis_wait)

# Go side: start Worker Pool to consume tasks
# Configure the same Redis keys in go_worker/main.go
```

### 3. Hybrid Pattern
Use CelestialTree tracing and Go Worker execution simultaneously for complete observability and high-performance execution capabilities.

## Best Practices

### 1. CelestialTree Configuration
- Deploy an independent CelestialTree service in production environments
- Adjust event sampling rate based on task volume
- Periodically clean up expired event data

### 2. Go Worker Deployment
- Choose an appropriate concurrency level based on task type
- Monitor Redis connection status and queue length
- Implement custom Processors for specific business logic

### 3. Error Handling
- Add comprehensive error logging for Go Worker
- Implement task retry and dead letter queue mechanisms
- Monitor CelestialTree connection status

### 4. Performance Tuning
- Adjust Redis connection pool size
- Optimize task payload serialization format
- Adjust Worker concurrency based on hardware resources

## Extension Suggestions

### 1. Adding New Processors
Add new Processor functions in `go_worker/worker/processors.go` to support more types of task processing.

### 2. Custom Parsers
Implement custom TaskParsers to support parsing of complex task formats.

### 3. Monitoring Integration
Integrate Go Worker metrics into the framework's monitoring system for unified observability.

### 4. Multi-Language Support
Following the Go Worker pattern, implement Worker components in other languages (e.g., Java, Rust).

## Notes

1. **Version Compatibility**: Ensure CelestialTree client and server versions are compatible
2. **Network Latency**: Network latency to Redis and CelestialTree will affect overall performance
3. **Resource Management**: Configure Worker concurrency appropriately to avoid resource contention
4. **Data Consistency**: Pay attention to the use of Redis transactions and atomic operations
5. **Security Considerations**: Protect access credentials for Redis and CelestialTree
