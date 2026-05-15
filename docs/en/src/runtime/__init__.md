# Runtime Module

> 📅 Last Updated: 2026/05/09

The Runtime module provides the task execution runtime environment for CelestialFlow, including core functionalities such as task scheduling, queue management, error handling, and performance monitoring. It serves as the infrastructure layer for actual task execution.

## Module Overview

The Runtime module manages the lifecycle of task execution, from task submission to result retrieval. It provides multiple execution modes (serial, parallel, asynchronous), robust error handling mechanisms, performance monitoring, and resource management features.

## File Descriptions

### Core Runtime Components

1. **core_dispatch.py** (`TaskDispatch`)
   - **Purpose**: Core task execution runner supporting multiple execution modes
   - **Execution Modes**:
     - Serial execution: Executes tasks sequentially
     - Thread pool: Concurrent execution for I/O-intensive tasks
     - Process pool: Concurrent execution for CPU-intensive tasks
     - Async execution: Asynchronous tasks based on asyncio
   - **Key Features**: Task scheduling, worker thread management, timeout control, resource cleanup

2. **core_queue.py** (`TaskInQueue`, `TaskOutQueue`)
   - **Purpose**: Task input/output queues for data transfer between nodes
   - **Queue Types**:
     - `TaskInQueue`: Task input queue, receives output from upstream nodes
     - `TaskOutQueue`: Task output queue, sends results to downstream nodes
   - **Key Features**: Thread safety, flow control, backpressure handling, serialization support

3. **core_envelope.py** (`TaskEnvelope`)
   - **Purpose**: Task data wrapper containing task data, metadata, and execution context
   - **Contains**: Task ID, input data, execution parameters, error handling strategy, priority
   - **Key Features**: Data encapsulation, context propagation, error propagation, priority sorting

### Monitoring and Metrics

4. **core_metrics.py** (`TaskMetrics`)
   - **Purpose**: Task execution metrics collection and monitoring
   - **Collected Metrics**: Execution time, success rate, error rate, queue length, throughput
   - **Key Features**: Real-time monitoring, performance analysis, bottleneck detection, alert triggering

### Tools and Utilities

5. **util_errors.py** (`CelestialFlowError`, `ConfigurationError`, `InvalidOptionError`, `ExecutionModeError`, `StageModeError`, `LogLevelError`, `RemoteWorkerError`, `UnconsumedError`)
   - **Purpose**: Error handling framework defining standard error types and handling strategies
   - **Error Types**: 
     - `CelestialFlowError`: Base class for all custom exceptions
     - `ConfigurationError`: Configuration errors (invalid parameters, unsupported combinations, etc.)
     - `InvalidOptionError`: Invalid configuration option value
     - `ExecutionModeError`: Execution mode error
     - `StageModeError`: Stage mode error
     - `LogLevelError`: Log level error
     - `RemoteWorkerError`: Remote worker error
     - `UnconsumedError`: Unconsumed task error
   - **Key Features**: Error classification, detailed error messages, parameter validation, error recovery

6. **util_factories.py**
   - **Purpose**: Factory functions for runtime components, simplifying object creation
   - **Factory Functions**:
     - `make_counter()`: Creates counters (thread-safe/process-safe)
     - `make_queue_backend()`: Creates queue backends based on execution mode
     - `make_task_in_queue()`: Creates task input queues
     - `make_task_out_queue()`: Creates task output queues
   - **Key Features**: Unified object creation interface, configuration adaptation, dependency management

7. **util_types.py**
   - **Purpose**: Runtime type definitions and data structures
   - **Included Types**:
     - `TerminationSignal`: Sentinel object for task queue termination
     - `TerminationIdPool`: Termination signal ID pool
     - `StageStatus`: Stage status enum (NOT_STARTED, RUNNING, STOPPED)
     - `STAGE_STYLE`: Stage style enum
     - `NodeLabelStyle`: Node label style (from CelestialTree)
   - **Key Features**: Type definitions, enum management, data structures, type safety

8. **util_queue.py**
   - **Purpose**: Runtime utility functions (`cleanup_mpqueue` was removed along with process mode)

9. **util_hash.py**
    - **Purpose**: Object hash computation for task deduplication and caching
    - **Key Functions**:
      - `make_hashable()`: Converts objects into hashable form
      - `object_to_str_hash()`: Computes string hash of objects
    - **Key Features**: Stable hash computation, object serialization, task deduplication, cache key generation

10. **util_estimators.py**
    - **Purpose**: Execution time estimation and progress calculation
    - **Key Functions**:
      - `calc_elapsed()`: Calculates elapsed time
      - `calc_remaining()`: Calculates remaining time
      - `calc_global_remain_equal_pred()`: Calculates global remaining time (equal-weight prediction)
    - **Key Features**: Time estimation, progress prediction, performance analysis, ETA calculation

## Module Relationships

### Internal Relationships
- `TaskDispatch` uses `TaskInQueue` and `TaskOutQueue` to get tasks and send results
- `TaskEnvelope` is passed through queues, containing the complete execution context
- `TaskMetrics` monitors the execution state of `TaskDispatch`
- All errors are handled uniformly through `CelestialFlowError` and its subclasses

### External Relationships
- **With Stage Module**: `TaskDispatch` executes `TaskExecutor` and `TaskStage`
- **With Graph Module**: Provides execution engine and communication mechanism for `TaskGraph`
- **With Persistence Module**: Supports persistence of execution state
- **With Observability Module**: Provides monitoring data and performance metrics

## Architecture Features

### Multi-Mode Execution
- Supports four execution modes for different scenario requirements
- Automatically selects optimal execution strategy
- Supports mixed execution modes

### Robustness Design
- Complete error handling chain
- Automatic retry and failover
- Resource leak protection

### Observability
- Comprehensive metrics collection
- Real-time progress reporting
- Detailed execution logs

### Extensibility
- Plugin-based architecture
- Custom execution strategies
- Configurable queue implementations

## Usage Patterns

### Basic Usage
1. **Create Runner**: Choose the appropriate `TaskDispatch` mode based on task type
2. **Configure Queues**: Set up input/output queues to establish data flow channels
3. **Execute Tasks**: Submit tasks to the runner and monitor execution state
4. **Process Results**: Retrieve results from output queue and handle errors

### Advanced Usage
1. **Custom Runner**: Inherit from `TaskDispatch` to implement specific execution logic
2. **Mixed Mode**: Combine different execution modes for complex workflows
3. **Monitoring Integration**: Integrate with external monitoring systems for centralized monitoring

## Best Practices

1. **I/O-Intensive Tasks**: Use thread pool mode
2. **CPU-Intensive Tasks**: Use process pool mode
3. **Async Tasks**: Use async mode for improved concurrency performance
4. **Critical Tasks**: Configure appropriate retry strategies and timeout settings
5. **Batch Tasks**: Use batch processing mode for improved throughput
6. **Monitoring Configuration**: Configure comprehensive monitoring and alerting for production environments
