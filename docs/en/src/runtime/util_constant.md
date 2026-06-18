# RuntimeConstant

> 📅 Last Updated: 2026/06/18

`runtime/util_constant.py` defines runtime global constants, primarily the log level mapping table `LEVEL_DICT`.

## Core Constants

### LEVEL_DICT

A mapping dictionary from log level names to numeric values, with higher values indicating higher priority. This constant is used by `LogInlet` for log filtering and level comparison — when `LogInlet`'s `log_level` is set to a certain level, all logs with numeric values lower than that level are discarded.

```python
LEVEL_DICT = {
    "TRACE": 0,
    "DEBUG": 10,
    "SUCCESS": 20,
    "INFO": 30,
    "WARNING": 40,
    "ERROR": 50,
    "CRITICAL": 60,
}
```

#### Level Hierarchy

```mermaid
flowchart TD
    subgraph Levels["Log Level Hierarchy - Higher value = higher priority"]
        direction TB
        CRI["CRITICAL (60)"]
        ERR["ERROR (50)"]
        WAR["WARNING (40)"]
        INF["INFO (30)"]
        SUC["SUCCESS (20)"]
        DEB["DEBUG (10)"]
        TRA["TRACE (0)"]
    end

    CRI --> ERR
    ERR --> WAR
    WAR --> INF
    INF --> SUC
    SUC --> DEB
    DEB --> TRA

    style CRI fill:#b71c1c,color:#fff
    style ERR fill:#f44336,color:#fff
    style WAR fill:#ff9800,color:#fff
    style INF fill:#2196f3,color:#fff
    style SUC fill:#4caf50,color:#fff
    style DEB fill:#9e9e9e,color:#fff
    style TRA fill:#e0e0e0
```

## Usage Example

### Log Level Filtering Logic

```python
from celestialflow.runtime.util_constant import LEVEL_DICT

# 1. View all levels and their values
for name, value in LEVEL_DICT.items():
    print(f"  {name:>8} = {value:>2}")

# 2. Simulate LogInlet's log filtering logic
log_level_name = "INFO"
current_level = LEVEL_DICT[log_level_name]

log_records = [
    ("DEBUG", "Debug information"),
    ("INFO", "User login successful"),
    ("WARNING", "Disk space low"),
    ("ERROR", "Database connection failed"),
    ("SUCCESS", "Data export successful"),
    ("CRITICAL", "System crash"),
]

filtered = [
    (name, msg)
    for name, msg in log_records
    if LEVEL_DICT.get(name, 0) >= current_level
]
# Result only retains INFO and above levels
print(filtered)
# [('INFO', 'User login successful'), ('WARNING', 'Disk space low'),
#  ('ERROR', 'Database connection failed'), ('CRITICAL', 'System crash')]

# 3. Level comparison helper function
def is_level_enabled(current: str, target: str) -> bool:
    return LEVEL_DICT.get(target, 0) >= LEVEL_DICT.get(current, 0)

print(is_level_enabled("WARNING", "ERROR"))    # True
print(is_level_enabled("INFO", "DEBUG"))        # False
```

### Log Level Validation

```python
from celestialflow.runtime.util_constant import LEVEL_DICT

# Validate whether a user-provided log level is valid
def validate_level(level: str) -> bool:
    return level in LEVEL_DICT

print(validate_level("INFO"))     # True
print(validate_level("VERBOSE"))  # False
```

## Notes

- `LEVEL_DICT` is the core basis for `LogInlet` log filtering; do not arbitrarily modify the numeric values.
- `STAGE_STYLE` depends on the `celestialtree` external package's `NodeLabelStyle`; the `{base}`, `{payload.name}`, `{type}` variables in the template string are injected by the CelestialTree rendering engine.
