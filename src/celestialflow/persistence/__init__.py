# persistence/__init__.py
"""CelestialFlow 持久化模块。

提供任务失败回退（Fallback）与运行日志（Log）的记录、写入与查询能力。
"""

from .core_fallback import (
    FallbackInlet,
    FallbackSpout,
    get_fallback_inlet,
    get_fallback_spout,
)
from .core_log import (
    LogInlet,
    LogSpout,
    get_log_inlet,
    get_log_spout,
)

__all__ = [
    "FallbackInlet",
    "FallbackSpout",
    "LogInlet",
    "LogSpout",
    "get_fallback_inlet",
    "get_fallback_spout",
    "get_log_inlet",
    "get_log_spout",
]
