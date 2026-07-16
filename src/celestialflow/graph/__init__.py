# graph/__init__.py
"""CelestialFlow 图模块。

提供任务图构建、连接、调度与预定义图结构（链、交叉、网格、环、轮、完全图）。
"""

from .core_graph import TaskGraph
from .core_structure import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGrid,
    TaskLoop,
    TaskWheel,
)

__all__ = [
    "TaskChain",
    "TaskComplete",
    "TaskCross",
    "TaskGraph",
    "TaskGrid",
    "TaskLoop",
    "TaskWheel",
]
