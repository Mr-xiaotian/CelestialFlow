# persist/__init__.py
"""CelestialFlow 持久化模块。

提供任务生命周期（Lifecycle）与运行日志（Log）的记录、写入与查询能力。
"""

from .core_lifecycle import (
    LifecycleInlet,
    LifecycleSpout,
)
from .core_log import (
    LogInlet,
    LogSpout,
)
from .core_run import (
    run_resources,
)

__all__ = [
    "LifecycleInlet",
    "LifecycleSpout",
    "LogInlet",
    "LogSpout",
    "run_resources",
]
