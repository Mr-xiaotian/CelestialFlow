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
def _pipeline(
    observers: ObserverHub,
    metrics_view: MetricsView,
    push_spout: PushSpout | None,
    injection_target: InjectionTarget | None,
) -> Generator[Path | None, None, None]:
    """
    共享运行管线：注册 ``lifecycle`` / ``log``（及可选上报）inlet，并统一管理
    全部 spout 与节拍器的启停。

    进入时创建并启动全部 spout；启用上报时，额外启动一个以
    :data:`_TICK_INTERVAL` 为基准周期的节拍器，把图级状态快照交给推送 inlet，
    并在提供注入目标时按拍从远程服务拉取任务注入。产出 lifecycle 数据库路径；
    退出时先停节拍器再统一停止 spout，保证运行期即使抛出异常也能完成回收。
    指标观察者须由调用方在进入本管线前注册到 ``observers``，本函数只把其只读
    视图交给 ``LogInlet`` 与快照处理器。

    :param observers: 接收全局 inlet 的观察者 hub
    :param metrics_view: 指标只读视图，供 ``LogInlet`` 与快照处理器查询
    :param push_spout: 已构建的推送 spout；``None`` 表示本次运行不上报
    :param injection_target: 任务注入目标；``None`` 表示本次运行不拉取注入
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    log_level = load_log_level_from_pyproject()

    lifecycle_spout = LifecycleSpout()
    log_spout = LogSpout()

    session: requests.Session | None = None
    ticker: Ticker | None = None
    observers.add_observer(LifecycleInlet().bind_spout(lifecycle_spout))
    observers.add_observer(LogInlet(metrics_view, log_level).bind_spout(log_spout))
    if push_spout is not None:
        push_inlet = PushInlet().bind_spout(push_spout)
        observers.add_observer(push_inlet)

        session = requests.Session()
        hub = TickHub()
        hub.add_handler(PushSnapshotHandler(metrics_view, push_inlet))
        if injection_target is not None:
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
    上报，才会注册 :class:`PushInlet`、启动 :class:`PushSpout` 并启动节拍器，把
    状态快照推送到远端、同时从远端拉取任务注入到 ``injection_target``
    （``report_url`` 未配置时回退到
    :data:`~celestialflow.runtime.util_config.DEFAULT_REPORT_URL`）。

    :param observers: 任务图自身的观察者 hub
    :param report_session_id: 上报会话标识，随记录一并提交给服务端
    :param metrics_view: 指标只读视图，供日志与快照处理器等消费者查询
    :param injection_target: 任务注入目标，通常是任务图自身
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    push_spout: PushSpout | None = None
    if load_if_report_from_pyproject():
        push_spout = PushSpout(report_session_id, load_report_url_from_pyproject())

    with _pipeline(
        observers, metrics_view, push_spout, injection_target
    ) as lifecycle_db_path:
        yield lifecycle_db_path


@contextmanager
def run_node_resources(
    observers: ObserverHub,
) -> Generator[Path | None, None, None]:
    """
    单节点运行期资源：内部创建并注册指标观察者，仅装配 ``lifecycle`` + ``log``。

    独立运行的节点不产生图结构、也不参与图级上报，因此本入口既不接收会话标识，
    也不装配推送通道或注入目标；指标观察者由本入口创建并注册，运行结束后无需
    外部持有。

    :param observers: 节点自身的观察者 hub
    :return: 进入时产出 lifecycle 数据库路径，未就绪时为 ``None``
    """
    metrics_view = MetricsObserver()
    observers.add_observer(metrics_view)

    with _pipeline(observers, metrics_view, None, None) as lifecycle_db_path:
        yield lifecycle_db_path
