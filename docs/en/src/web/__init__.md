# Web Module

> 📅 Last updated: 2026/04/22

The Web module provides CelestialFlow's web-based monitoring and management interface. Built on FastAPI, it supports real-time task status display, error monitoring, task injection, and remote control capabilities.

## Module Overview

The Web module is a standalone web server that provides a visual monitoring and management interface for CelestialFlow. It receives status data from `TaskReporter`, provides real-time monitoring views, and supports task injection and system control through the web interface.

## File Descriptions

### Core Components

1. **core_server.py** (`TaskWebServer`)
   - **Purpose**: FastAPI-based web server providing RESTful API endpoints
   - **Key Features**:
     - **Status Display**: Real-time display of task graph structure, stage status, and performance metrics
     - **Error Monitoring**: Display of error details, stack traces, and occurrence timelines
     - **Task Injection**: Dynamically inject new tasks into a running task graph via the web interface
     - **Remote Control**: Support for pause, resume, restart, and terminate operations
     - **Historical Analysis**: View historical execution records and performance trends
   - **Tech Stack**: FastAPI, Jinja2 templates, static file serving

### Utility Components

2. **util_cal.py**
   - **Purpose**: Calculation utility functions that convert millisecond refresh intervals to seconds and clamp the range

3. **util_config.py**
   - **Purpose**: Loading and saving frontend configuration files (JSON)

4. **util_error.py**
   - **Purpose**: Utility functions for error query parameter normalization, filtering, and pagination

## Module Dependencies

### Internal Dependencies
- `TaskWeb` is the sole core component of the Web module
- Contains frontend static files (HTML, CSS, JavaScript) and backend API services

### External Dependencies
- **With Observability Module**: Receives status data reported by `TaskReporter`
- **With Graph Module**: Displays task graph structure and stage status
- **With Runtime Module**: Displays execution status and performance metrics
- **With Stage Module**: Displays task stage details and execution results
- **With Persistence Module**: Accesses persisted logs and error data

## Architecture Features

### Frontend-Backend Separation
- **Backend**: FastAPI provides RESTful API services
- **Frontend**: Static HTML/JS/CSS files supporting modern browsers
- **Communication**: JSON over HTTP, with status updates via periodic polling

### Real-Time Support
- **Periodic Polling**: Frontend periodically requests status updates at a configurable interval
- **Version-Based Caching**: Supports a `known_rev` parameter; returns `data=null` when unchanged, reducing transfer volume

### Extensibility
- **Plugin Architecture**: Supports custom monitoring panels and controls
- **Theme System**: Supports interface theme switching and customization
- **Multilingual**: Supports internationalized interfaces
- **Permission System**: Role-based access control

### Security
- **CORS Configuration**: Controls cross-origin access
- **Authentication & Authorization**: Supports multiple authentication methods (API Key, OAuth, JWT)
- **Input Validation**: Strict input data validation and sanitization
- **Rate Limiting**: Prevents API abuse

## Feature Highlights

### Monitoring Dashboard
- **Topology View**: Visual display of task graph structure and dependencies
- **Status Panel**: Real-time display of stage status (color-coded)
- **Performance Dashboard**: Displays CPU, memory, queue length, and other metrics
- **Error Center**: Centralized display of error information and statistics

### Control Features
- **Task Injection**: Define new tasks via forms or JSON
- **Parameter Adjustment**: Dynamically adjust system parameters and configuration
- **Execution Control**: Start, pause, resume, and terminate task execution
- **Data Export**: Export execution logs, performance data, and error reports

### Analysis Features
- **Historical Trends**: View historical trends of performance metrics
- **Comparative Analysis**: Compare execution across different time periods
- **Root Cause Analysis**: Error root cause analysis and correlation analysis
- **Report Generation**: Automatically generate execution reports and performance analysis reports

## Usage Patterns

### Starting the Server
```bash
# Command-line startup
celestialflow-web

# Specify port and host
celestialflow-web --host 0.0.0.0 --port 5080
```

### API Usage
```python
import requests

# Get task graph status
response = requests.get("http://localhost:5000/api/pull_status")
status = response.json()

# Inject new tasks (POST to push_injection_tasks, then pulled by TaskGraph)
task_injection = {
    "node": "Stage 1",
    "task_datas": [[1, 2, 3]],
    "timestamp": "2024-01-01T00:00:00"
}
response = requests.post("http://localhost:5000/api/push_injection_tasks", json=task_injection)
```

## Deployment Considerations

### Server Configuration
- **Process Management**: Use WSGI/ASGI servers such as Gunicorn or Uvicorn
- **Load Balancing**: Configure load balancing for multi-instance deployments
- **Reverse Proxy**: Use Nginx or Apache as a reverse proxy
- **SSL/TLS**: Configure HTTPS to secure data transmission

### Performance Optimization
- **Static File Caching**: Configure browser caching strategies
- **API Caching**: Cache frequently accessed API responses
- **Connection Pooling**: Database and external service connection pooling
- **Compression**: Enable Gzip/Brotli compression

### High Availability
- **Multi-Instance Deployment**: Deploy multiple web server instances
- **Session Sharing**: Configure shared session storage (Redis)
- **Health Checks**: Configure health check endpoints
- **Failover**: Configure automatic failover mechanisms

## Best Practices

### Development Environment
1. **Hot Reload**: Enable code hot reloading during development for improved efficiency
2. **Debugging Tools**: Integrate debugging tools and performance profilers
3. **Mock Data**: Provide mock data generation tools for frontend development
4. **API Documentation**: Maintain complete API documentation and examples

### Production Environment
1. **Security Hardening**: Disable debug mode, configure security headers, regularly update dependencies
2. **Monitoring Integration**: Integrate system monitoring and log collection
3. **Backup Strategy**: Regularly back up configuration and important data
4. **Capacity Planning**: Plan server resources based on user volume and data volume

### User Experience
1. **Responsive Design**: Support desktop and mobile device access
2. **Loading Optimization**: Optimize initial load speed and page responsiveness
3. **Error Handling**: Provide friendly error messages and recovery guidance
4. **Help Documentation**: Provide online help and operation guides

### Maintenance and Upgrades
1. **Version Management**: Clear version release and upgrade processes
2. **Data Migration**: Support safe migration of configuration and data
3. **Rollback Plans**: Prepare version rollback plans to address upgrade issues
4. **User Notification**: Notify users in advance of important changes
