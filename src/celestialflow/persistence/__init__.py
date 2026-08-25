# persistence/__init__.py
"""CelestialFlow 持久化模块。

提供任务生命周期（Lifecycle）与运行日志（Log）的记录、写入与查询能力。
"""

from .core_lifecycle import (
    LifecycleInlet,
    LifecycleSpout,
    get_lifecycle_inlet,
    get_lifecycle_spout,
)
from .core_log import (
    LogInlet,
    LogSpout,
    get_log_inlet,
    get_log_spout,
)
from .core_scope import funnel_scope

__all__ = [
    "LifecycleInlet",
    "LifecycleSpout",
    "LogInlet",
    "LogSpout",
    "funnel_scope",
    "get_lifecycle_inlet",
    "get_lifecycle_spout",
    "get_log_inlet",
    "get_log_spout",
]
