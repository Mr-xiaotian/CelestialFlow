# assembly/core_run.py
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import requests

from ..observer import MetricsObserver, ObserverHub
from ..persist.core_lifecycle import LifecycleInlet, LifecycleSpout
from ..persist.core_log import LogInlet, LogSpout
from ..reporter import (
    InjectionHandler,
    InjectionTarget,
    PushInlet,
    PushSnapshotHandler,
    PushSpout,
)
from ..runtime.util_config import (
    load_if_report_from_pyproject,
    load_log_level_from_pyproject,
    load_report_url_from_pyproject,
)
from ..runtime.util_types import MetricsView
from ..ticker import Ticker, TickHub

_TICK_INTERVAL: float = 1.0
"""节拍器基准周期（秒）。各处理器以自己的 ``tick_period`` 缩放出实际周期。"""


@contextmanager
def run_graph_resources(
    observers: ObserverHub,
    report_session_id: str,
    metrics_view: MetricsView,
    injection_target: InjectionTarget,
) -> Generator[Path | None, None, None]:
    """
    任务图运行期资源：``lifecycle`` + ``log``，并按 ``if_report`` 决定是否追加
    远程上报与注入。

    指标写模型由任务图持有并已注册到 ``observers``，本入口只把其只读视图交给
    ``LogInlet`` 与快照处理器。上报开关从项目级 ``pyproject.toml`` 的
    ``[tool.celestialflow]`` 节读取：仅当 ``if_report`` 显式配置为 ``true`` 时启用
    上报，才会注册 :class:`PushInlet`、启动 :class:`PushSpout` 并启动一个以
    :data:`_TICK_INTERVAL` 为基准周期的节拍器，把状态快照推送到远端，同时按拍从
    远端拉取任务注入到 ``injection_target``（``report_url`` 未配置时回退到
    :data:`~celestialflow.runtime.util_config.DEFAULT_REPORT_URL`）。

    退出时先停节拍器再统一停止 spout，保证运行期即使抛出异常也能完成回收。

    :param observers: 任务图自身的观察者 hub
    :param report_session_id: 上报会话标识，随记录一并提交给服务端
    :param metrics_view: 指标只读视图，供日志与快照处理器等消费者查询
    :param injection_target: 任务注入目标，通常是任务图自身
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    log_level = load_log_level_from_pyproject()

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()
    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet(metrics_view, log_level).bind_spout(log_spout))

    push_spout: PushSpout | None = None
    session: requests.Session | None = None
    ticker: Ticker | None = None
    if load_if_report_from_pyproject():
        push_spout = PushSpout(report_session_id, load_report_url_from_pyproject())
        push_inlet = PushInlet().bind_spout(push_spout)
        observers.add_observer(push_inlet)

        session = requests.Session()
        hub = TickHub()
        hub.add_handler(PushSnapshotHandler(metrics_view, push_inlet))
        hub.add_handler(
            InjectionHandler(
                push_spout.base_url,
                push_spout.graph_id,
                injection_target,
                session,
            )
        )
        ticker = Ticker(_TICK_INTERVAL, hub, name="report")

    try:
        lifecycle_spout.start()
        log_spout.start()
        if push_spout is not None:
            push_spout.start()
        if ticker is not None:
            ticker.start()
        yield lifecycle_spout.db_path
    finally:
        if ticker is not None:
            ticker.stop()
        lifecycle_spout.stop()
        log_spout.stop()
        if push_spout is not None:
            push_spout.stop()
        if session is not None:
            session.close()


@contextmanager
def run_node_resources(
    observers: ObserverHub,
) -> Generator[Path | None, None, None]:
    """
    单节点运行期资源：内部创建并注册指标观察者，仅装配 ``lifecycle`` + ``log``。

    独立运行的节点不产生图结构、也不参与图级上报，因此本入口既不接收会话标识，
    也不装配推送通道、节拍器或注入目标；指标观察者由本入口创建并注册，运行结束后
    无需外部持有。退出时统一停止 spout，保证运行期即使抛出异常也能完成回收。

    :param observers: 节点自身的观察者 hub
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    log_level = load_log_level_from_pyproject()

    metrics_view = MetricsObserver()
    observers.add_observer(metrics_view)

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()
    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet(metrics_view, log_level).bind_spout(log_spout))

    try:
        lifecycle_spout.start()
        log_spout.start()
        yield lifecycle_spout.db_path
    finally:
        lifecycle_spout.stop()
        log_spout.stop()
