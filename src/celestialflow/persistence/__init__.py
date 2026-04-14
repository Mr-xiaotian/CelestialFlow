# persistence/__init__.py
from .core_funnel import BaseSpout, BaseInlet
from .core_fail import FailSpout, FailInlet
from .core_log import LogSpout, LogInlet

__all__ = [
    "BaseSpout",
    "BaseInlet",
    "FailSpout",
    "FailInlet",
    "LogSpout",
    "LogInlet",
]
