# assembly/core_run.py
from __future__ import annotations

import uuid
from collections.abc import Generator
from contextlib import contextmanager

from ..observer import MetricsObserver, ObserverHub
from ..persist import LifecycleObserver, LogObserver
from ..reporter import (
    InjectionTarget,
    InjectionTicker,
    PushObserver,
    SnapshotTicker,
)
from ..runtime import ReportConfig
from ..runtime.util_log_level import normalize_log_level
from ..ticker import TickClock, TickHub


@contextmanager
def run_reporting_resources(
    observers: ObserverHub,
    tickers: TickHub,
    injection_target: InjectionTarget,
    *,
    log_level: str,
    interval: float,
    report: ReportConfig,
) -> Generator[None, None, None]:
    """
    带远程上报的任务图运行期资源：``metrics`` + ``lifecycle`` + ``log``，
    外加 ``report`` 驱动的状态快照上报、任务注入与节拍时钟。

    指标写模型由本入口创建并注册到 ``observers``，其只读视图交给
    :class:`LogObserver` 与快照 ticker。本入口自行生成一个不透明的上报会话标识，
    注册 :class:`PushObserver`，并把 :class:`SnapshotTicker` 与
    :class:`InjectionTicker` 注册进 ``tickers``。

    进入时依次启动观察者、ticker 资源与时钟，保证第一拍到达时上报通道与各 ticker
    均已就绪；退出时按 ``clock.stop()`` → ``tickers.stop()`` → ``observers.stop()``
    的逆序回收，避免推送通道关闭后仍有快照入队。

    :param observers: 运行主体自身的观察者 hub
    :param tickers: 运行主体自身的节拍 hub，上报用的 ticker 会注册到这里
    :param injection_target: 任务注入目标，通常是任务图自身
    :param log_level: :class:`LogObserver` 的日志过滤级别，默认
        ``DEFAULT_LOG_LEVEL``
    :param report: 远程上报配置，必填
    :param interval: 时钟基准周期（秒），各 ticker 以 ``tick_period`` 缩放
    :return: ``None``
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    log_level = normalize_log_level(log_level)
    session_id = uuid.uuid4().hex

    metrics = MetricsObserver()
    lifecycle = LifecycleObserver()
    log = LogObserver(metrics, log_level)
    push = PushObserver(session_id, report.url, metrics)

    observers.add_observer(metrics)
    observers.add_observer(lifecycle)
    observers.add_observer(log)
    observers.add_observer(push)

    tickers.add_ticker(SnapshotTicker(metrics, push))
    tickers.add_ticker(
        InjectionTicker(
            report.url,
            session_id,
            injection_target,
        )
    )

    clock = TickClock(interval, tickers)
    try:
        observers.start()
        tickers.start()
        clock.start()
        yield None
    finally:
        try:
            clock.stop()
        finally:
            try:
                tickers.stop()
            finally:
                observers.stop()


@contextmanager
def run_local_resources(
    observers: ObserverHub,
    tickers: TickHub,
    *,
    log_level: str,
    interval: float,
) -> Generator[None, None, None]:
    """
    本地运行期资源：内部创建并注册指标观察者，仅装配 ``lifecycle`` + ``log``，
    并驱动运行主体自身的节拍 hub。

    适用于独立运行的节点与未启用上报的任务图：这类运行不产生跨进程上报，
    因此本入口既不接收上报配置，也不装配推送通道或注入目标；指标观察者
    由本入口创建并注册，运行结束后无需外部持有。节拍部分与上报入口一致：
    启动 ticker 资源后由时钟驱动，退出时逆序回收。

    :param observers: 运行主体自身的观察者 hub
    :param tickers: 运行主体自身的节拍 hub
    :param log_level: :class:`LogObserver` 的日志过滤级别，默认
        ``DEFAULT_LOG_LEVEL``
    :param interval: 时钟基准周期（秒），各 ticker 以 ``tick_period`` 缩放
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

    clock = TickClock(interval, tickers)
    try:
        observers.start()
        tickers.start()
        clock.start()
        yield None
    finally:
        try:
            clock.stop()
        finally:
            try:
                tickers.stop()
            finally:
                observers.stop()
