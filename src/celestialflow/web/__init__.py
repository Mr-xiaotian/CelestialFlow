# web/__init__.py
"""CelestialFlow Web 服务模块。

提供基于 FastAPI 的任务可视化 Web 服务。
"""

from .core_server import TaskWebServer

__all__ = [
    "TaskWebServer",
]
