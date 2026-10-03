# assembly/__init__.py
"""CelestialFlow 运行期资源装配模块。

负责把 lifecycle / log / 上报三类全局 funnel 观察者注册到运行期 hub，
并统一管理其 spout 的启停。
"""

from .core_run import run_resources

__all__ = [
    "run_resources",
]
