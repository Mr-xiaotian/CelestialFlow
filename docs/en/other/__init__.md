# Other Module

> 📅 Last updated: 2026/04/22

## Overview

The Other module contains extension components and external integrations for the CelestialFlow framework. These components are not part of the core framework but provide important extended functionality. It mainly includes two components: CelestialTree Client and Go Worker, used for task provenance tracking and cross-language task execution, respectively.

## File Details

### 1. ctree_client.md - CelestialTree Client

**Purpose**: Integrate with the CelestialTree event sourcing system to enable full-chain task tracing and event recording.

**Core Features**:
- **Event Recording**: Automatically records key events during a task's lifecycle (input, success, failure, retry, split, route, etc.)
- **Data Lineage Tracking**: Query the data sources and generation paths of results
- **Error Root Cause Localization**: Trace the complete call chain of failed tasks
- **Execution Tree Visualization**: Generate call tree structures of task execution

**Key Characteristics**:
- Integrates with CelestialTree service, supporting HTTP and gRPC communication
- Automatic event emission without manual instrumentation
- Provides simplified provenance query interfaces
- Supports complex scenarios such as task splitting, routing, and duplicate detection

**Usage Pattern**:
```python
# Configure CelestialTree client
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)

# Query provenance information
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
error_trace = graph.get_error_trace(error_id=12345)
```

### 2. go_worker.md - Go Worker Task Consumer

**Purpose**: A lightweight, concurrently scalable Redis-based task consumer (Worker Pool) for cross-language task execution.

**Core Features**:
- **Task Consumption**: Continuously consume tasks from Redis queues
- **Concurrent Execution**: Execute tasks with controllable concurrency
- **Result Write-back**: Write execution results back to Redis
- **Cross-language Support**: Serve as a Go-language execution node for TaskGraph

**Architecture Highlights**:
- **Worker Pool Pattern**: Uses goroutines and channels for concurrency control
- **Automatic Reconnection**: Supports exponential backoff retry on Redis connection failure
- **Pluggable Design**: Parser and Processor can be customized and extended
- **Generic Task Structure**: Uses JSON-formatted task payloads

**Key Components**:
- **TaskParser**: Parses task payloads and converts them to the format required by the Processor
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
   - Works in conjunction with `TaskRedisTransport` and `TaskRedisAck` nodes from the `runtime` module
   - Communicates with the Python-side TaskGraph via Redis
   - Can be used as a standalone component without mandatory dependency on the core framework

### Component Collaboration

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **Task Execution Flow**:
   - TaskGraph generates tasks and writes them to Redis
   - Go Worker consumes tasks from Redis and executes them
   - Execution results are written back to Redis, and TaskGraph reads the results
   - CelestialTree Client records events throughout the entire process

2. **Data Flow**:
   - Task data is transferred between Python and Go via Redis
   - Event data is sent to CelestialTree via HTTP/gRPC
   - Provenance queries are retrieved from CelestialTree through the client API

## Architecture Highlights

### 1. Loosely Coupled Design
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
- Automatic reconnection ensures system stability

## Usage Patterns

### 1. Full-Chain Tracing Pattern
```python
# Enable CelestialTree tracing
graph.set_ctree(use_ctree=True)

# Run the task graph
graph.start_graph(init_tasks)

# Query task provenance
trace = graph.get_stage_input_trace("ProcessingStage")
```

### 2. Cross-Language Execution Pattern
```python
# Python side: Define Redis transport nodes
redis_sink = TaskRedisTransport(key="tasks:input")
redis_ack = TaskRedisAck(key="tasks:output")

# Go side: Start Worker Pool to consume tasks
# Configure the same Redis key in go_worker/main.go
```

### 3. Hybrid Pattern
Use CelestialTree tracing and Go Worker execution simultaneously to achieve complete observability and high-performance execution capability.

## Best Practices

### 1. CelestialTree Configuration
- Deploy a standalone CelestialTree service in production environments
- Adjust the event sampling rate based on task volume
- Periodically clean up expired event data

### 2. Go Worker Deployment
- Choose appropriate concurrency levels based on task types
- Monitor Redis connection status and queue length
- Implement custom Processors for specific business logic

### 3. Error Handling
- Add comprehensive error logging for Go Worker
- Implement task retry and dead letter queue mechanisms
- Monitor CelestialTree connection status

### 4. Performance Tuning
- Adjust Redis connection pool size
- Optimize serialization format for task payloads
- Adjust Worker concurrency based on hardware resources

## Extension Suggestions

### 1. Adding New Processors
Add new Processor functions in `go_worker/worker/processors.go` to support more types of task processing.

### 2. Custom Parsers
Implement custom TaskParsers to support parsing of complex task formats.

### 3. Monitoring Integration
Integrate Go Worker metrics into the framework's monitoring system for unified observability.

### 4. Multi-Language Support
Following the Go Worker pattern, implement Worker components in other languages (such as Java, Rust).

## Notes

1. **Version Compatibility**: Ensure CelestialTree client and server versions are compatible
2. **Network Latency**: Network latency of Redis and CelestialTree will affect overall performance
3. **Resource Management**: Configure Worker concurrency appropriately to avoid resource contention
4. **Data Consistency**: Pay attention to the use of Redis transactions and atomic operations
5. **Security Considerations**: Protect access credentials for Redis and CelestialTree
