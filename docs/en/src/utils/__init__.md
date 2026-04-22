# Utils Module

The Utils module provides general-purpose utility functions and helper classes for CelestialFlow, including performance benchmarking, data cloning, collection operations, debugging tools, and formatting capabilities. These tools are widely used by other modules, improving code reusability and maintainability.

## Module Overview

The Utils module contains a series of independent yet practical tools, each focused on solving specific general-purpose problems. These tools are designed to be stateless, testable, and composable, and can be used anywhere in the project.

## File Descriptions

### Performance Tools

1. **util_benchmark.py**
   - **Purpose**: Performance benchmarking tool for comparing performance differences across execution modes
   - **Key Features**:
     - Execution time measurement and statistics
     - Memory usage monitoring
     - Concurrency performance testing
     - Performance comparison report generation
   - **Use Cases**: 
     - Optimizing task execution mode selection
     - Identifying performance bottlenecks
     - Verifying parallelization effectiveness
     - Capacity planning and resource allocation

### Data Processing Tools

2. **util_clone.py**
   - **Purpose**: Deep cloning tool supporting complete copying of complex objects
   - **Key Features**:
     - Recursive object cloning
     - Circular reference handling
     - Custom cloning strategies
     - Performance optimization (caching, lazy cloning)
   - **Supported Types**: Primitive types, lists, dicts, sets, custom objects, nested structures
   - **Use Cases**: Task data copying, state snapshots, test data preparation

3. **util_collections.py**
   - **Purpose**: Collection operation tool providing specific data processing functionality
   - **Key Function**: `cluster_by_value_sorted()`: Clusters and sorts a dictionary by value
   - **Key Features**:
     - Group dictionary entries by value
     - Sort grouped results
     - Return clustered results sorted by value
   - **Use Cases**: Data analysis, result grouping, statistical aggregation, performance metric clustering

### Development and Debugging Tools

4. **util_debug.py**
   - **Purpose**: Debugging tool for identifying serialization issues
   - **Key Function**: `find_unpickleable()`: Finds parts of an object that cannot be pickled
   - **Key Features**:
     - Recursively checks object serializability
     - Identifies specific attributes causing pickle failures
     - Provides detailed error information
     - Helps debug serialization issues in multiprocessing environments
   - **Use Cases**: Multiprocess task execution, object serialization debugging, cross-process communication troubleshooting

5. **util_format.py**
   - **Purpose**: Data formatting and display tool for improved readability
   - **Key Functions**:
     - `format_repr()`: Formats an object's string representation with a maximum length limit
     - `format_table()`: Formats tabular data with alignment and borders
     - `format_duration()`: Formats time intervals (converts seconds to a readable format)
     - `format_timestamp()`: Formats timestamps
     - `format_avg_time()`: Formats average processing time
   - **Key Features**: Data beautification, table generation, time formatting, performance metric display
   - **Use Cases**: Log output, performance reports, benchmark result display, debug information formatting

## Module Dependencies

### Internal Dependencies
- All tools are independent and can be used standalone
- Some tools have interdependencies (e.g., `util_debug` may use `util_format` for output)
- Tools follow a consistent interface convention

### External Dependencies
- **With All Modules**: The Utils module is widely used by all other modules
- **With Runtime Module**: Performance testing tools are used to test executor performance
- **With Stage Module**: Data cloning tools are used for task state copying
- **With Graph Module**: Collection tools are used for graph data operations
- **With Persistence Module**: Formatting tools are used for data serialization display

## Design Principles

### Single Responsibility
- Each tool file addresses only one category of problems
- Functions are designed to be small and focused, avoiding feature bloat
- Clear interfaces and well-defined responsibilities

### Stateless Design
- Tool functions are stateless whenever possible
- Avoids global variables and side effects
- Supports concurrent-safe usage

### Testability
- Pure function design for easy unit testing
- Dependency injection support
- Mock and stub support

### Extensibility
- Plugin-based architecture supporting custom extensions
- Configuration-driven with flexible behavior adjustments
- Version compatibility guarantees

## Usage Patterns

### Direct Usage
```python
from celestialflow.utils import util_benchmark, util_clone, util_collections

# Performance testing
results = util_benchmark.run_benchmark(task_executor, iterations=100)

# Deep cloning
cloned_data = util_clone.deep_clone(complex_object)

# Collection operations
grouped = util_collections.cluster_by_value_sorted(items)
```

### Integrated Usage
- Integrate performance monitoring into task executors
- Use collection tools in data pipelines
- Enable diagnostic tools in debug mode
- Use formatting tools in report generation

### Custom Extensions
- Inherit base tool classes to implement specific functionality
- Add custom formatters
- Implement domain-specific collection operations

## Best Practices

1. **Performance-Critical Paths**: Avoid using heavy tools (such as deep cloning) in hot paths
2. **Error Handling**: Tool functions should provide clear error messages and recovery options
3. **Resource Management**: Tools requiring resources (such as file handles, network connections) should clean up properly
4. **Documentation and Examples**: Provide usage examples and common scenarios for complex tools
5. **Version Compatibility**: Keep tool interfaces backward-compatible, avoiding breaking changes
6. **Test Coverage**: Ensure tool functions have comprehensive test coverage, especially for edge cases
