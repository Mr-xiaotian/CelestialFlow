# assembly/core_run.py
from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager

from ..observer import MetricsObserver, ObserverHub
from ..persist import LifecycleObserver, LogObserver
from ..reporter import (
    InjectionHandler,
    InjectionTarget,
    PushInlet,
    PushSnapshotHandler,
    PushSpout,
)
from ..runtime import ReportConfig
from ..runtime.util_log_level import DEFAULT_LOG_LEVEL, normalize_log_level
from ..ticker import Ticker, TickHub

_TICK_INTERVAL: float = 1.0
"""节拍器基准周期（秒）。各处理器以自己的 ``tick_period`` 缩放出实际周期。"""


@contextmanager
def run_reporting_resources(
    observers: ObserverHub,
    injection_target: InjectionTarget,
    *,
    log_level: str = DEFAULT_LOG_LEVEL,
    report: ReportConfig,
) -> Generator[None, None, None]:
    """
    带远程上报的任务图运行期资源：``metrics`` + ``lifecycle`` + ``log``，
    外加 ``report`` 驱动的状态快照上报与任务注入。

    指标写模型由本入口创建并注册到 ``observers``，其只读视图交给
    :class:`LogObserver` 与快照处理器。本入口自行生成一个不透明的上报会话标识，
    注册 :class:`PushInlet` 与 :class:`PushSnapshotHandler`，并通过
    ``observers.start()`` 启动持久化观察者、启动 :class:`PushSpout`，随后启动一个
    以 :data:`_TICK_INTERVAL` 为基准周期的节拍器，按拍把状态快照推送到
    ``report.url``（并在图结束时补推一次终态快照），同时按拍从远端拉取任务注入到
    ``injection_target``。节拍器会随其处理器一同启停注入处理器持有的 HTTP 会话。

    退出时先停节拍器（同时关闭注入会话），再通过 ``observers.stop()`` 逆序停止
    持久化观察者，最后停止推送通道并关闭其会话，保证运行期即使抛出异常也能完成回收。

    :param observers: 任务图自身的观察者 hub
    :param injection_target: 任务注入目标，通常是任务图自身
    :param log_level: :class:`LogObserver` 的日志过滤级别，默认
        ``DEFAULT_LOG_LEVEL``
    :param report: 远程上报配置，必填
    :return: ``None``
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    log_level = normalize_log_level(log_level)

    metrics_view = MetricsObserver()
    lifecycle = LifecycleObserver()
    log = LogObserver(metrics_view, log_level)

    observers.add_observer(metrics_view)
    observers.add_observer(lifecycle)
    observers.add_observer(log)

    session_id = uuid.uuid4().hex
    push_spout = PushSpout(session_id, report.url)
    push_inlet = PushInlet().bind_spout(push_spout)

    hub = TickHub()
    snapshot_handler = PushSnapshotHandler(metrics_view, push_inlet)
    hub.add_handler(snapshot_handler)
    hub.add_handler(
        InjectionHandler(
            push_spout.base_url,
            session_id,
            injection_target,
        )
    )
    ticker = Ticker(_TICK_INTERVAL, hub, name="report")

    # 快照处理器同时观察 GraphEndEvent 补推终态快照；注册在 PushInlet 之前，
    # 保证终态快照先于 shutdown_session 入队。
    observers.add_observer(snapshot_handler)
    observers.add_observer(push_inlet)

    try:
        observers.start()
        push_spout.start()
        ticker.start()
        yield None
    finally:
        # 先停节拍器（同时关闭注入会话），避免其在 HTTP 会话关闭后仍发起注入请求；
        # 再停止观察者，最后停止推送通道。
        ticker.stop()
        observers.stop()
        push_spout.stop()


@contextmanager
def run_local_resources(
    observers: ObserverHub,
    *,
    log_level: str = DEFAULT_LOG_LEVEL,
) -> Generator[None, None, None]:
    """
    本地运行期资源：内部创建并注册指标观察者，仅装配 ``lifecycle`` + ``log``。

    适用于独立运行的节点与未启用上报的任务图：这类运行不产生跨进程上报，
    因此本入口既不接收上报配置，也不装配推送通道、节拍器或注入目标；指标观察者
    由本入口创建并注册，运行结束后无需外部持有。进入时通过 ``observers.start()``
    启动观察者，退出时逆序停止，保证运行期即使抛出异常也能完成回收。

    :param observers: 运行主体自身的观察者 hub
    :param log_level: :class:`LogObserver` 的日志过滤级别，默认
        ``DEFAULT_LOG_LEVEL``
    :return: ``None``
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    log_level = normalize_log_level(log_level)

    metrics_view = MetricsObserver()
    lifecycle = LifecycleObserver()
    log = LogObserver(metrics_view, log_level)

    observers.add_observer(metrics_view)
    observers.add_observer(lifecycle)
    observers.add_observer(log)

    try:
        observers.start()
        yield None
    finally:
        observers.stop()
