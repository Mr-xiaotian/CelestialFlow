# Persistence Module

> 📅 Last updated: 2026/04/22

The Persistence module provides data persistence features for CelestialFlow, including execution log recording, error information storage, task state saving, and configuration constant management. It ensures that critical data from task execution can be reliably saved and retrieved.

## Module Overview

The Persistence module is responsible for persisting runtime data to various storage backends, supporting log recording, error tracking, state snapshots, and configuration management. The module adopts a spout pattern that seamlessly integrates into the task execution flow without affecting main flow performance.

## File Descriptions

### Log Persistence

1. **core_log.py** (`LogSpout`, `LogInlet`)
   - **Purpose**: Infrastructure for log recording and storage
   - **Core Components**:
     - `LogSpout`: Log spout that receives log messages from a queue and writes them to files
     - `LogInlet`: Log collector that writes logs to files
   - **Log Format**: Text log format containing timestamps, log levels, and message content
   - **Key Features**: Asynchronous writing, file management, log rotation, multi-process safety

### Error Persistence

2. **core_fail.py** (`FailSpout`, `FailInlet`)
   - **Purpose**: Infrastructure for error information recording and storage
   - **Core Components**:
     - `FailSpout`: Error spout that receives error information from a queue and writes it to files
     - `FailInlet`: Error collector that writes error information to files
   - **Error Information**: Error type, stack trace, context data, occurrence time, task ID
   - **Key Features**: Error classification, file storage, asynchronous processing, multi-process safety

### Success Result Persistence

3. **core_success.py** (`SuccessSpout`)
   - **Purpose**: Success result listener thread that continuously reads the success result queue and caches task-result pairs
   - **Core Components**:
     - `SuccessSpout`: Inherits from `BaseSpout`, caches (task, result) pairs
   - **Key Features**: Success result caching, task-result pair extraction

### Data Format and Configuration

4. **util_jsonl.py**
   - **Purpose**: JSON Lines format support for efficient structured data storage and reading
   - **Key Features**:
     - `load_jsonl_logs()`: Load log data from JSONL files with support for selective field reading
     - Streaming data reading with support for starting from a specified line number
     - Data filtering and transformation
     - Error handling and file validation
   - **Use Cases**: Log file reading, error record analysis, Web UI data display

5. **util_constant.py**
   - **Purpose**: Persistence-related constants and configuration definitions
   - **Contents**:
     - `LEVEL_DICT`: Log level dictionary defining log levels and their corresponding numeric values
     - Log levels include: TRACE(0), DEBUG(10), SUCCESS(20), INFO(30), WARNING(40), ERROR(50), CRITICAL(60)
   - **Key Features**: Unified log level management, level comparison, log filtering

## Module Relationships

### Internal Relationships
- All persistence classes inherit from `BaseSpout`/`BaseInlet` (defined in the Funnel module)
- `LogSpout`/`LogInlet` and `FailSpout`/`FailInlet` are used in pairs
- `SuccessSpout` is used independently to cache success results
- Utility classes are used by core classes to provide format support and configuration management

### External Relationships
- **With Runtime Module**: Listens to logs and errors produced at runtime
- **With Stage Module**: Records task execution status and results
- **With Graph Module**: Saves graph structure state and execution history
- **With Observability Module**: Provides raw data for monitoring and analysis
- **With Utils Module**: Uses utility functions for data processing and formatting

## Architecture Features

### Asynchronous Non-blocking Design
- Spouts run in background threads without blocking the main flow
- Queue buffering to handle write peaks
- Batch commits to improve storage efficiency

### Multi-backend Support
- Supports files, databases, remote services, and other storage types
- Unified interface for easy switching and extension
- Storage adapter pattern supporting custom backends

### Reliability Guarantees
- Write failure retry mechanism
- Data integrity verification
- Storage space monitoring and alerting
- Graceful degradation without affecting the main flow

### Configurability
- Storage paths are configurable
- Format and encoding are adjustable
- Performance parameters are tunable
- Alert rules are customizable

## Usage Patterns

### Basic Configuration
```python
from celestialflow.persistence import LogSpout, LogInlet, FailSpout, FailInlet

# Configure log persistence
log_spout = LogSpout()
log_spout.start()
log_inlet = LogInlet(log_spout.get_queue())

# Configure error persistence
fail_spout = FailSpout(error_source="graph_errors")
fail_spout.start()
fail_inlet = FailInlet(fail_spout.get_queue())
```

### Advanced Usage
1. **Multi-backend Storage**: Write to files and databases simultaneously for redundant storage
2. **Custom Formats**: Implement custom serialization formats
3. **Real-time Alerting**: Configure error thresholds to trigger real-time notifications
4. **Data Archiving**: Automatically archive historical data to free storage space
5. **Data Migration**: Migrate data between different storage backends

### Monitoring and Maintenance
1. **Storage Monitoring**: Monitor disk usage to prevent storage overflow
2. **Performance Monitoring**: Monitor write latency and throughput
3. **Error Monitoring**: Monitor persistence failure rates
4. **Data Cleanup**: Periodically clean up expired data

## Best Practices

### Production Environment Configuration
1. **Storage Planning**: Plan storage space based on data volume and retention policies
2. **Redundancy Design**: Use multi-replica storage for important data
3. **Performance Optimization**: Adjust batch processing size and concurrency based on load
4. **Monitoring and Alerting**: Configure comprehensive monitoring and alerting rules

### Development and Testing
1. **Local Storage**: Use file storage in the development environment for easy debugging
2. **Mock Backends**: Use in-memory or mock backends in the testing environment
3. **Data Isolation**: Use different storage paths for different environments
4. **Cleanup Strategy**: Automatically clean up test data to prevent accumulation

### Fault Handling
1. **Write Failures**: Configure appropriate retry strategies and fallback plans
2. **Full Storage**: Monitor storage space and configure automatic cleanup
3. **Network Failures**: Handle network interruptions for remote storage
4. **Format Errors**: Data validation and format compatibility handling
