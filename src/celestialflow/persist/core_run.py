# persist/core_run.py
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from ..observer import ObserverHub
from ..reporter import NullPushSpout, PushInlet, PushSpout
from ..runtime.util_config import (
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
)
from .core_lifecycle import LifecycleInlet, LifecycleSpout
from .core_log import LogInlet, LogSpout


@contextmanager
def run_resources(
    observers: ObserverHub, report_session_id: str
) -> Generator[Path | None, None, None]:
    """
    运行期资源上下文：注册全局 funnel 观察者并启停 ``lifecycle`` / ``log`` /
    上报推送 spout。

    进入时创建并启动全局 spout，将其绑定的 inlet 注册到 ``observers``，
    并产出 lifecycle 数据库路径；退出时统一停止所有 spout，保证运行期即使
    抛出异常也能完成回收。

    ``LogInlet`` 的日志级别从项目级 ``pyproject.toml`` 的
    ``[tool.celestialflow]`` 节读取（见
    :func:`~celestialflow.runtime.util_config.load_log_level_from_pyproject`）。
    上报地址同样从该节读取：配置了 ``url`` 时使用 :class:`PushSpout`，
    否则回退到 :class:`NullPushSpout`。

    :param observers: 接收全局 inlet 的观察者 hub，通常为任务图或任务节点自身的 hub
    :param report_session_id: 上报会话标识，随记录一并提交给服务端
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    report_url = load_report_url_from_pyproject()

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()
    if report_url is not None:
        report_spout = PushSpout(report_session_id, report_url)
    else:
        report_spout = NullPushSpout()

    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(
        LogInlet(load_log_level_from_pyproject()).bind_spout(log_spout)
    )
    observers.add_observer(PushInlet().bind_spout(report_spout))

    try:
        lifecycle_spout.start()
        log_spout.start()
        report_spout.start()
        yield lifecycle_spout.db_path
    finally:
        lifecycle_spout.stop()
        log_spout.stop()
        report_spout.stop()
