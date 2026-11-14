# reporter/core_snapshot.py
from __future__ import annotations

from typing import Any, Protocol

from ..runtime.util_types import MetricsView
from ..ticker import TickEvent, TickHandler
from .util_snapshot import to_status_snapshot


class SnapshotSink(Protocol):
    """快照写入目标协议。

    只暴露快照入队语义，不暴露推送通道与 spout 细节，从而让快照处理器与具体
    上报实现解耦。:class:`~celestialflow.reporter.core_push.PushObserver` 满足本协议。
    """

    def push_snapshot(self, snapshot: dict[str, dict[str, Any]]) -> None: ...


class PushSnapshotHandler(TickHandler):
    """按拍把图级状态快照交给推送通道的处理器。

    按拍（:class:`~celestialflow.ticker.core_handler.TickHandler`）从
    :class:`~celestialflow.runtime.util_types.MetricsView` 读取整图指标，经
    :func:`~celestialflow.reporter.util_snapshot.to_status_snapshot` 投影为状态载荷后
    写入 :class:`~celestialflow.reporter.core_push.PushObserver`，由推送 spout 异步发送。

    本处理器只负责周期性快照；图结束时的终态快照与会话下线由
    :class:`~celestialflow.reporter.core_push.PushObserver` 在 ``GraphEndEvent`` 中按序
    补推。本处理器只做投影与入队，不进行任何网络 IO。
    """

    def __init__(self, metrics_view: MetricsView, sink: SnapshotSink) -> None:
        """
        初始化快照推送处理器。

        :param metrics_view: 指标只读视图
        :param sink: 快照写入目标，通常是
            :class:`~celestialflow.reporter.core_push.PushObserver`
        """
        self._metrics_view = metrics_view
        self._sink = sink

    def on_tick(self, event: TickEvent) -> None:
        """
        读取并推送一次图级状态快照。

        :param event: 当前节拍事件
        """
        snapshot = to_status_snapshot(self._metrics_view.get_graph_metrics())
        self._sink.push_snapshot(snapshot)
