# funnel/__init__.py
"""CelestialFlow 漏斗模块。

提供数据收集器（Inlet）与监听器（Spout）的基础抽象。
"""

from .core_inlet import BaseInlet
from .core_spout import BaseSpout

__all__ = [
    "BaseInlet",
    "BaseSpout",
]
