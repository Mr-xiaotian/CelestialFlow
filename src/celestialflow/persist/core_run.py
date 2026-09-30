# persist/core_run.py
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from ..observer import ObserverHub
from .core_lifecycle import LifecycleInlet, LifecycleSpout
from .core_log import LogInlet, LogSpout


@contextmanager
def run_resources(
    observers: ObserverHub,
) -> Generator[Path | None, None, None]:
    """
    运行期资源上下文：注册全局 funnel 观察者并启停 ``lifecycle`` / ``log`` spout。

    进入时创建并启动两个全局 spout，将其绑定的 inlet 注册到 ``observers``，
    并产出 lifecycle 数据库路径；退出时统一停止两个 spout，保证运行期即使
    抛出异常也能完成回收。

    :param observers: 接收全局 inlet 的观察者 hub，通常为任务图或任务节点自身的 hub
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()

    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet().bind_spout(log_spout))

    try:
        lifecycle_spout.start()
        log_spout.start()
        yield lifecycle_spout.db_path
    finally:
        lifecycle_spout.stop()
        log_spout.stop()
