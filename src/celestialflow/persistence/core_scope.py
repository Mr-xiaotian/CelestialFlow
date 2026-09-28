from __future__ import annotations

from ..observability.core_hub import ObserverHub
from ..observability.core_observer import Observer
from .core_lifecycle import get_lifecycle_inlet, get_lifecycle_spout
from .core_log import get_log_inlet, get_log_spout


def attach_funnel_observers(*hubs: ObserverHub) -> tuple[Observer, Observer]:
    """
    将全局 lifecycle / log 观察者注册到给定 hub。

    :param hubs: 需要接收 funnel 事件的观察者 hub
    :return: ``(lifecycle_observer, log_observer)`` 引用，供后续注销
    :rtype: tuple[Observer, Observer]
    """
    lifecycle_observer: Observer = get_lifecycle_inlet()
    log_observer: Observer = get_log_inlet()

    for hub in hubs:
        hub.add_observer(lifecycle_observer)
        hub.add_observer(log_observer)

    return lifecycle_observer, log_observer


def detach_funnel_observers(
    observers: tuple[Observer, Observer], *hubs: ObserverHub
) -> None:
    """
    从给定 hub 注销全局 lifecycle / log 观察者。

    :param observers: :func:`attach_funnel_observers` 返回的观察者引用
    :param hubs: 需要注销观察者的 hub
    """
    lifecycle_observer, log_observer = observers

    for hub in hubs:
        hub.remove_observer(log_observer)
        hub.remove_observer(lifecycle_observer)


def open_funnel() -> None:
    """
    启动全局 ``lifecycle`` / ``log`` spout。

    由顶层运行入口（``BaseTaskNode.run`` / ``TaskGraph.run`` 等）在注入任务前显式调用，
    与 :func:`close_funnel` 成对使用。
    """
    get_lifecycle_spout().start()
    get_log_spout().start()


def close_funnel() -> list[Exception]:
    """
    停止全局 ``lifecycle`` / ``log`` spout。

    :return: 收尾阶段收集到的异常列表
    :rtype: list[Exception]
    """
    error_list: list[Exception] = []

    try:
        get_log_spout().stop()
    except Exception as exception:
        error_list.append(exception)

    try:
        get_lifecycle_spout().stop()
    except Exception as exception:
        error_list.append(exception)

    return error_list
