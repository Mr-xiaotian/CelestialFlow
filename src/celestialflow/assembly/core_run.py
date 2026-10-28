# assembly/core_run.py
from __future__ import annotations

import uuid
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
from ..runtime.core_config import ReportConfig, normalize_log_level
from ..ticker import Ticker, TickHub

_TICK_INTERVAL: float = 1.0
"""节拍器基准周期（秒）。各处理器以自己的 ``tick_period`` 缩放出实际周期。"""


@contextmanager
def run_graph_resources(
    observers: ObserverHub,
    injection_target: InjectionTarget,
    *,
    log_level: str = "INFO",
    report: ReportConfig | None = None,
) -> Generator[Path | None, None, None]:
    """
    任务图运行期资源：``metrics`` + ``lifecycle`` + ``log``，并按 ``report``
    决定是否追加远程上报与注入。

    指标写模型由本入口创建并注册到 ``observers``，其只读视图交给 ``LogInlet``
    与快照处理器。上报配置由调用方显式传入：``report is None`` 时不上报；
    否则本入口自行生成一个不透明的上报会话标识，注册 :class:`PushInlet` 与
    :class:`PushSnapshotHandler`、启动 :class:`PushSpout` 并启动一个以
    :data:`_TICK_INTERVAL` 为基准周期的节拍器，按拍把状态快照推送到
    ``report.url``（并在图结束时补推一次终态快照），同时按拍从远端拉取任务
    注入到 ``injection_target``。

    退出时先停节拍器再统一停止 spout，保证运行期即使抛出异常也能完成回收。

    :param observers: 任务图自身的观察者 hub
    :param injection_target: 任务注入目标，通常是任务图自身
    :param log_level: ``LogInlet`` 的日志过滤级别，默认 ``"INFO"``
    :param report: 远程上报配置；``None`` 表示不上报，默认 ``None``
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    log_level = normalize_log_level(log_level)

    metrics_view = MetricsObserver()
    observers.add_observer(metrics_view)

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()
    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet(metrics_view, log_level).bind_spout(log_spout))

    push_spout: PushSpout | None = None
    session: requests.Session | None = None
    ticker: Ticker | None = None
    if report is not None:
        session_id = uuid.uuid4().hex
        push_spout = PushSpout(session_id, report.url)
        push_inlet = PushInlet().bind_spout(push_spout)

        session = requests.Session()
        hub = TickHub()
        snapshot_handler = PushSnapshotHandler(metrics_view, push_inlet)
        hub.add_handler(snapshot_handler)
        hub.add_handler(
            InjectionHandler(
                push_spout.base_url,
                session_id,
                injection_target,
                session,
            )
        )
        ticker = Ticker(_TICK_INTERVAL, hub, name="report")

        # 快照处理器同时观察 on_graph_end 补推终态快照；注册在 PushInlet 之前，
        # 保证终态快照先于 shutdown_session 入队。
        observers.add_observer(snapshot_handler)
        observers.add_observer(push_inlet)

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
    *,
    log_level: str = "INFO",
) -> Generator[Path | None, None, None]:
    """
    单节点运行期资源：内部创建并注册指标观察者，仅装配 ``lifecycle`` + ``log``。

    独立运行的节点不产生图结构、也不参与图级上报，因此本入口既不接收上报配置，
    也不装配推送通道、节拍器或注入目标；指标观察者由本入口创建并注册，运行结束后
    无需外部持有。退出时统一停止 spout，保证运行期即使抛出异常也能完成回收。

    :param observers: 节点自身的观察者 hub
    :param log_level: ``LogInlet`` 的日志过滤级别，默认 ``"INFO"``
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    log_level = normalize_log_level(log_level)

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
