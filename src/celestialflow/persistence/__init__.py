# persistence/__init__.py
from .core_fallback import FallbackInlet, FallbackSpout
from .core_log import LogInlet, LogSpout
from .core_success import SuccessSpout

__all__ = [
    "FallbackInlet",
    "FallbackSpout",
    "LogInlet",
    "LogSpout",
    "SuccessSpout",
]
