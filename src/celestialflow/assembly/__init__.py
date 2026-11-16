# assembly/__init__.py
"""CelestialFlow 运行期资源装配模块。

负责把 lifecycle / log / 上报三类全局 funnel 观察者注册到运行期 hub，
并统一管理其 spout 的启停；同时按需装配节拍时钟并驱动运行主体的 ticker hub。
"""

from .core_run import run_local_resources, run_reporting_resources

__all__ = [
    "run_local_resources",
    "run_reporting_resources",
]
