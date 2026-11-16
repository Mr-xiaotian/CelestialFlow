# ticker/__init__.py
"""CelestialFlow 节拍器模块。

提供时间源（:class:`TickClock`）、节拍事件（:class:`TickEvent`）、可分发的 hub
（:class:`TickHub`）与定时器叶子（:class:`Ticker`）。时钟只负责产生时间并在装配
层驱动节拍树的根，hub 负责按 ``tick_period`` 过滤后逐层分发，叶子负责响应。本模块
与事件驱动的 ``observer`` / ``funnel`` 相互独立，可在使用处按需组合。
"""

from .core_clock import DEFAULT_TICK_INTERVAL, TickClock
from .core_event import TickEvent
from .core_hub import TickHub
from .core_ticker import Ticker

__all__ = [
    "DEFAULT_TICK_INTERVAL",
    "TickClock",
    "TickEvent",
    "TickHub",
    "Ticker",
]
