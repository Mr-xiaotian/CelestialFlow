# observer/core_observer.py
from __future__ import annotations

import traceback

from .core_event import (
    GraphEndEvent,
    GraphStartEvent,
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


class Observer:
    """执行器生命周期观察者基类。

    所有回调均提供默认空实现，实现方继承本基类即可只覆写关心的方法。
    :class:`~celestialflow.observer.core_hub.ObserverHub` 在转发事件时捕获回调
    抛出的异常，并交由该观察者自身的 :meth:`handle_exception` 处理，不会逃逸到框架
    执行路径。
    """

    def on_node_added(self, node: str) -> None:
        """
        节点加入任务图回调。

        该回调发生在图构建期（:meth:`~celestialflow.graph.core_graph.TaskGraph.set_nodes`），
        用于让需要感知图结构的观察者（如指标存储器）预先建立每节点存储。

        :param node: 加入任务图的节点名称
        """
        ...

    def on_node_connected(self, from_node: str, to_node: str) -> None:
        """
        节点建立连接回调。

        该回调发生在图构建期（:meth:`~celestialflow.graph.core_graph.TaskGraph.connect`），
        用于让需要感知图结构的观察者预先建立边级存储。实现应为幂等。

        :param from_node: 上游节点名称
        :param to_node: 下游节点名称
        """
        ...

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

    def on_task_retry(self, event: TaskRetryEvent) -> None:
        """
        任务重试回调。

        :param event: 任务重试事件
        """
        ...

    def on_termination_input(self, event: TerminationInputEvent) -> None:
        """
        终止信号输入回调。

        :param event: 终止信号输入事件
        """
        ...

    def on_termination_merge(self, event: TerminationMergeEvent) -> None:
        """
        终止信号合并回调。

        :param event: 终止信号合并事件
        """
        ...

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        """
        工作器崩溃回调。

        :param event: 工作器崩溃事件
        """
        ...

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        节点结束回调。

        :param event: 节点结束事件
        """
        ...

    def on_graph_start(self, event: GraphStartEvent) -> None:
        """
        任务图启动回调。

        :param event: 任务图启动事件
        """
        ...

    def on_graph_end(self, event: GraphEndEvent) -> None:
        """
        任务图结束回调。

        :param event: 任务图结束事件
        """
        ...

    def handle_exception(self, exception: Exception) -> None:
        """
        观察者回调自身抛出异常时的处理回调。

        :class:`~celestialflow.observer.core_hub.ObserverHub` 在转发事件时，
        若本观察者的某个回调抛出异常，会调用本方法进行处理。默认实现将异常
        回溯打印到标准错误；子类可覆写以实现自定义策略（如收集、上报或忽略）。

        若本方法自身也抛出异常，则由 hub 的 ``handle_exception`` 作为最终兜底处理。

        :param exception: 观察者回调抛出的异常
        """
        traceback.print_exception(exception)
