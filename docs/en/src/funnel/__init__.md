# Funnel Module

The Funnel module provides the queue communication infrastructure for CelestialFlow and serves as the base classes for `LogSpout`/`LogInlet` and `FailSpout`/`FailInlet` in the Persistence module.

## Module Overview

The Funnel module adopts the Spout/Inlet (outlet/inlet) pattern to implement multi-process-safe asynchronous queue communication. Inlets are responsible for writing records to the queue, while Spouts read and process records from the queue in a background thread.

## File Description

### Core Components

1. **core_spout.py** (`BaseSpout`)
   - **Purpose**: Base class for all outlet classes, providing background thread listening and queue consumption functionality
   - **Key Features**: Background thread listening, graceful start/stop, multi-process-safe queues

2. **core_inlet.py** (`BaseInlet`)
   - **Purpose**: Base class for all inlet classes, providing queue write functionality
   - **Key Features**: Queue write encapsulation

## Inheritance Hierarchy

```
BaseSpout (funnel/core_spout.py)
├── LogSpout (persistence/core_log.py)
├── FailSpout (persistence/core_fail.py)
└── SuccessSpout (persistence/core_success.py)

BaseInlet (funnel/core_inlet.py)
├── LogInlet (persistence/core_log.py)
└── FailInlet (persistence/core_fail.py)
```

## Module Relationships

### External Relationships
- **With Persistence Module**: `LogSpout`/`LogInlet`, `FailSpout`/`FailInlet`, and `SuccessSpout` all inherit from this module's base classes
- **With Runtime Module**: Uses `TerminationSignal` as the stop signal and `cleanup_mpqueue` for queue cleanup
