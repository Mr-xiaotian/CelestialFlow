# assembly/core_run.py
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from ..observer import ObserverHub
from ..persist.core_lifecycle import LifecycleInlet, LifecycleSpout
from ..persist.core_log import LogInlet, LogSpout
from ..reporter import (
    NullPushSpout,
    PushInlet,
    PushSpout,
)
from ..runtime.util_config import (
    load_if_report_from_pyproject,
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
)
from ..runtime.util_types import MetricsView


@contextmanager
def run_resources(
    observers: ObserverHub,
    report_session_id: str,
    metrics_view: MetricsView,
) -> Generator[Path | None, None, None]:
    """
    运行期资源上下文：注册全局 funnel 观察者并启停 ``lifecycle`` / ``log`` /
    错误推送与图元信息推送 spout。

    进入时创建并启动全局 spout，将其绑定的 inlet 注册到 ``observers``，
    并产出 lifecycle 数据库路径；退出时统一停止所有 spout，保证运行期即使
    抛出异常也能完成回收。

    指标写模型由调用方（任务图或任务节点）持有并已注册到 ``observers``，
    本函数只把其只读视图注入给需要的消费者（如 ``LogInlet``）。

    ``LogInlet`` 的日志级别从项目级 ``pyproject.toml`` 的
    ``[tool.celestialflow]`` 节读取（见
    :func:`~celestialflow.runtime.util_config.load_log_level_from_pyproject`）。
    上报开关同样从该节读取：仅当 ``if_report`` 显式配置为 ``true`` 时启用上报，
    并使用 :class:`PushSpout`（``report_url`` 未配置时回退到
    :data:`~celestialflow.runtime.util_config.DEFAULT_REPORT_URL`）；
    否则一律回退到 :class:`NullPushSpout`。

    :param observers: 接收全局 inlet 的观察者 hub，通常为任务图或任务节点自身的 hub
    :param report_session_id: 上报会话标识，随记录一并提交给服务端
    :param metrics_view: 指标只读视图，供日志等消费者查询
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    if_report = load_if_report_from_pyproject()
    report_url = load_report_url_from_pyproject()
    log_level = load_log_level_from_pyproject()

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()
    if if_report:
        report_spout = PushSpout(report_session_id, report_url)
    else:
        report_spout = NullPushSpout()

    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet(metrics_view, log_level).bind_spout(log_spout))
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
