# observability/core_hub.py
from __future__ import annotations

import traceback
from threading import Lock

from ..runtime.util_errors import ConfigurationError
from .core_event import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
    TerminationInputEvent,
    TerminationMergeEvent,
    WorkerCrashEvent,
)
from .core_observer import Observer


class ObserverHub(Observer):
    """观察者分发中心。

    本身即 :class:`Observer`，将收到的每个事件按注册顺序显式转发给已注册的观察者。
    单个观察者回调抛出的异常会被捕获并打印，不会中断其余观察者的分发，
    也不会逃逸到框架执行路径。
    """

    def __init__(self) -> None:
        """初始化分发中心。"""
        self._observers: list[Observer] = []
        self._lock = Lock()

    # ==== 注册 ====

    def add_observer(self, observer: Observer) -> None:
        """
        注册用户观察者。

        :param observer: 待注册的观察者
        :raises ConfigurationError: 注册会形成 hub 循环引用
        """
        self._reject_cycle(observer)
        with self._lock:
            self._observers.append(observer)

    def _snapshot(self) -> list[Observer]:
        """
        返回当前观察者快照。

        :return: 观察者快照列表
        """
        with self._lock:
            return list(self._observers)

    def _reject_cycle(self, observer: Observer) -> None:
        """
        拒绝会形成 hub 循环引用的注册，避免分发时无限递归。

        :param observer: 待注册的观察者
        :raises ConfigurationError: 该观察者已（间接）持有当前 hub
        """
        if observer is self:
            raise ConfigurationError("cannot register an ObserverHub into itself")
        if not isinstance(observer, ObserverHub):
            return

        stack: list[ObserverHub] = [observer]
        seen: set[int] = set()
        while stack:
            hub = stack.pop()
            if id(hub) in seen:
                continue
            seen.add(id(hub))
            if hub is self:
                raise ConfigurationError(
                    "cyclic ObserverHub registration detected: cannot register a hub "
                    "into a hub that already (directly or transitively) contains it"
                )
            stack.extend(
                child for child in hub._snapshot() if isinstance(child, ObserverHub)
            )

    # ==== 分发 ====

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        转发节点启动事件。

        :param event: 节点启动事件
        """
        for observer in self._snapshot():
            try:
                observer.on_node_start(event)
            except Exception:
                traceback.print_exc()

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        转发任务输入事件。

        :param event: 任务输入事件
        """
        for observer in self._snapshot():
            try:
                observer.on_task_input(event)
            except Exception:
                traceback.print_exc()

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        转发任务成功事件。

        :param event: 任务成功事件
        """
        for observer in self._snapshot():
            try:
                observer.on_task_success(event)
            except Exception:
                traceback.print_exc()

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        转发任务失败事件。

        :param event: 任务失败事件
        """
        for observer in self._snapshot():
            try:
                observer.on_task_fail(event)
            except Exception:
                traceback.print_exc()

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        转发任务跳过事件。

        :param event: 任务跳过事件
        """
        for observer in self._snapshot():
            try:
                observer.on_task_skip(event)
            except Exception:
                traceback.print_exc()

    def on_task_retry(self, event: TaskRetryEvent) -> None:
        """
        转发任务重试事件。

        :param event: 任务重试事件
        """
        for observer in self._snapshot():
            try:
                observer.on_task_retry(event)
            except Exception:
                traceback.print_exc()

    def on_termination_input(self, event: TerminationInputEvent) -> None:
        """
        转发终止信号输入事件。

        :param event: 终止信号输入事件
        """
        for observer in self._snapshot():
            try:
                observer.on_termination_input(event)
            except Exception:
                traceback.print_exc()

    def on_termination_merge(self, event: TerminationMergeEvent) -> None:
        """
        转发终止信号合并事件。

        :param event: 终止信号合并事件
        """
        for observer in self._snapshot():
            try:
                observer.on_termination_merge(event)
            except Exception:
                traceback.print_exc()

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        """
        转发工作器崩溃事件。

        :param event: 工作器崩溃事件
        """
        for observer in self._snapshot():
            try:
                observer.on_worker_crash(event)
            except Exception:
                traceback.print_exc()

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        转发节点结束事件。

        :param event: 节点结束事件
        """
        for observer in self._snapshot():
            try:
                observer.on_node_end(event)
            except Exception:
                traceback.print_exc()
