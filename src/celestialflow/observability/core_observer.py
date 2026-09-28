# observability/core_observer.py
from __future__ import annotations

from typing import Protocol

from .core_event import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)


class Observer(Protocol):
    """执行器生命周期观察者协议。

    所有回调均提供默认空实现，实现方继承本协议即可只覆写关心的方法。
    回调中的异常由 :class:`~celestialflow.observability.core_hub.ObserverHub`
    统一捕获，不会逃逸到框架执行路径。
    """

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        节点启动回调。

        :param event: 节点启动事件
        """
        ...

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        任务输入回调。

        :param event: 任务输入事件
        """
        ...

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        任务成功回调。

        :param event: 任务成功事件
        """
        ...

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        任务失败回调。

        :param event: 任务失败事件
        """
        ...

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        任务跳过回调。

        :param event: 任务跳过事件
        """
        ...

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        节点结束回调。

        :param event: 节点结束事件
        """
        ...
