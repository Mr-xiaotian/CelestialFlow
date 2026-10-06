# ticker/__init__.py
"""CelestialFlow 节拍器模块。

提供基于时间驱动的节拍器（Ticker）、节拍事件、处理器接口与分发中心。
本模块与事件驱动的 ``observer`` / ``funnel`` 相互独立，可在使用处按需组合。
"""

from .core_event import TickEvent
from .core_handler import TickHandler
from .core_hub import TickHub
from .core_ticker import Ticker

__all__ = [
    "TickEvent",
    "TickHandler",
    "TickHub",
    "Ticker",
]
