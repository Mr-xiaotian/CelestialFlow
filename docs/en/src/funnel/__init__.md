# Funnel Module

> 📅 Last Updated: 2026/05/09

The Funnel module provides the queue communication infrastructure for CelestialFlow and serves as the base classes for `LogSpout`/`LogInlet` and `FailSpout`/`FailInlet` in the Persistence module.

## Module Overview

The Funnel module adopts the Spout/Inlet (output/input) pattern to implement multi-process-safe asynchronous queue communication. Inlet is responsible for writing records to the queue, while Spout reads and processes records from the queue in a background thread.

## File Description

### Core Components

1. **core_spout.py** (`BaseSpout`)
   - **Purpose**: Base class for all spout classes, providing background thread listening and queue consumption functionality
   - **Key Features**: Background thread listening, graceful start/stop, multi-process-safe queue

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

## Module Dependencies

### External Dependencies
- **Persistence Module**: `LogSpout`/`LogInlet`, `FailSpout`/`FailInlet`, `SuccessSpout` all inherit from base classes in this module
- **Runtime Module**: Uses `TerminationSignal` as the stop signal
