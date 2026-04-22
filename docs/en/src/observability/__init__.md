# Observability Module

The Observability module provides observability features for CelestialFlow, including runtime status monitoring, performance metric collection, error tracking, and remote control. It makes the task execution process transparent, monitorable, and controllable.

## Module Overview

The Observability module is responsible for collecting, aggregating, and reporting system runtime status, providing real-time monitoring views and remote control capabilities. Through this module, users can monitor task execution status, performance metrics, and error information in real time, and dynamically adjust system behavior.

## File Descriptions

### Core Components

1. **core_report.py** (`TaskReporter`)
   - **Purpose**: Task status reporter that collects runtime status and reports it to a remote Web server
   - **Key Features**:
     - **Status Reporting**: Periodically pushes task graph structure, topology, runtime status, and error information
     - **Task Injection**: Receives user-injected new tasks from the Web UI and dynamically inserts them into the running task graph
     - **Parameter Adjustment**: Pulls configuration from the server to dynamically adjust reporting intervals and other parameters
     - **Error Synchronization**: Supports two error push modes (metadata mode and content mode)
   - **Communication Protocol**: HTTP
   - **Data Format**: JSON

2. **core_progress.py** (`TaskProgress`, `NullTaskProgress`)
   - **Purpose**: Task progress visualization based on `tqdm`
   - **Key Features**:
     - Dynamically update total task count (`add_total`)
     - Normal mode (`tqdm`) and async mode (`tqdm.asyncio`)
     - `NullTaskProgress` null implementation for when the progress bar is disabled

## Module Relationships

### Internal Relationships
- `TaskReporter` is the sole core component of the Observability module
- Designed to be pluggable and can be enabled or disabled as needed

### External Relationships
- **With Graph Module**: Collects task graph structure and topology information
- **With Runtime Module**: Collects execution status, performance metrics, and error information
- **With Stage Module**: Monitors task node execution status and results
- **With Persistence Module**: Retrieves persisted log and error data
- **With Web Module**: Bidirectional communication with the Web UI, supporting status display and remote control

## Architecture Features

### Bidirectional Communication
- **Upstream Channel**: Status data reported to the Web server
- **Downstream Channel**: Control commands sent from the Web server to the running instance
- **Real-time**: Supports real-time status updates and immediate control

### Incremental Updates
- Status data reported incrementally to reduce network traffic
- Error logs synchronized incrementally to avoid duplicate transmission
- Configuration changes applied incrementally to reduce restart requirements

### Fault-tolerant Design
- Local caching and retry during network interruptions
- Data integrity verification and repair
- Graceful degradation without affecting the main execution flow

### Security
- Reverse proxy with authentication layer recommended for production environments
- No sensitive data transmitted; restricting Web server access scope is recommended

## Data Model

### Status Data
- **Graph Structure**: Node list, dependency relationships, configuration parameters
- **Runtime Status**: Node states (pending, running, completed, failed), progress percentage
- **Performance Metrics**: Execution time, throughput, resource utilization, queue length
- **Error Information**: Error type, occurrence time, stack trace, impact scope

### Control Commands
- **Task Injection**: New task definitions, insertion positions, dependency relationships
- **Parameter Adjustment**: Reporting interval, log level, performance thresholds
- **Operation Commands**: Pause, resume, restart, terminate
- **Configuration Updates**: Runtime configuration, business parameters, resource limits

## Usage Patterns

### Basic Configuration
```python
from celestialflow.observability import TaskReporter
from celestialflow.persistence import LogInlet

# Create reporter
reporter = TaskReporter(
    host="127.0.0.1",  # Web server host
    port=5000,         # Web server port
    task_graph=my_task_graph,
    log_inlet=log_inlet  # LogInlet instance
)

# Start reporter
reporter.start()

# During task execution, the reporter automatically collects and reports status
```

### Advanced Features
1. **Custom Data Collection**: Implement custom data collectors to extend monitoring dimensions
2. **Multi-server Reporting**: Report to multiple monitoring servers simultaneously for redundancy
3. **Local Storage**: Temporarily store data locally when the network is unavailable, and sync when it recovers
4. **Data Filtering**: Configure data filtering rules to reduce unnecessary data transmission
5. **Alert Integration**: Integrate with external alerting systems for automated alerts

### Web UI Integration
1. **Real-time Monitoring**: View task execution status in real time through the Web UI
2. **Historical Analysis**: View historical execution records and performance trends
3. **Error Diagnosis**: View error details and root cause analysis
4. **Remote Control**: Dynamically adjust system behavior through the Web UI
5. **Report Generation**: Automatically generate execution reports and performance analyses

## Deployment Considerations

### Network Configuration
- **Bandwidth Requirements**: Evaluate bandwidth needs based on data volume and reporting frequency
- **Latency Tolerance**: Configure appropriate timeout and retry strategies
- **Firewall**: Ensure monitoring ports are accessible
- **Proxy Support**: Supports communication through proxy servers

### Security Configuration
- **Certificate Management**: Configure TLS certificates and keys
- **Authentication Mechanisms**: Configure API keys, tokens, or other authentication methods
- **Access Control**: Configure IP whitelists and rate limiting
- **Data Encryption**: Encrypt sensitive data in transit and at rest

### Performance Optimization
- **Batch Processing**: Batch report data to reduce request count
- **Compression**: Compress data in transit to reduce bandwidth usage
- **Caching**: Cache frequently accessed data locally
- **Asynchronous Processing**: Non-blocking data collection and reporting

## Best Practices

### Production Environment
1. **High Availability Deployment**: Deploy multiple monitoring servers to avoid single points of failure
2. **Data Retention Policy**: Configure data retention periods based on requirements
3. **Capacity Planning**: Plan storage and compute resources based on monitoring data volume
4. **Disaster Recovery**: Develop contingency plans for network interruptions and server failures

### Development and Testing
1. **Local Simulation**: Use a local mock server in the development environment
2. **Data Anonymization**: Use anonymized data in the testing environment
3. **Performance Testing**: Test the performance impact of large-scale data reporting
4. **Fault Testing**: Test recovery capabilities from network interruptions and server failures

### Monitoring and Maintenance
1. **Self-monitoring**: Monitor the reporter's own operational status
2. **Data Quality**: Monitor the completeness and accuracy of reported data
3. **Performance Monitoring**: Monitor reporting latency, success rate, and other metrics
4. **Security Auditing**: Periodically audit access logs and security events
