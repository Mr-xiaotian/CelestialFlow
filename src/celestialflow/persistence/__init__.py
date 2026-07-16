# persistence/__init__.py
"""CelestialFlow 持久化模块。

提供任务失败回退（Fallback）与运行日志（Log）的记录、写入与查询能力。
"""

from .core_fallback import FallbackInlet, FallbackSpout
from .core_log import LogInlet, LogSpout

__all__ = [
    "FallbackInlet",
    "FallbackSpout",
    "LogInlet",
    "LogSpout",
]
