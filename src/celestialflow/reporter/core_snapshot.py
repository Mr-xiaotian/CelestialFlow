# reporter/core_snapshot.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..observer import GraphEndEvent, Observer
from ..runtime.util_types import MetricsView, NodeMetrics
from ..ticker import TickEvent, TickHandler
from .core_push import PushInlet


def to_status_snapshot(
    metrics: Mapping[str, NodeMetrics],
) -> dict[str, dict[str, Any]]:
    """
    将整图节点指标投影为状态推送载荷。

    :param metrics: 节点名称到指标快照的映射
    :return: 节点名称到状态字典的映射
    """
    return {
        node: {
            "start_time": node_metrics.start_time,
            "status": node_metrics.status,
            "tasks_input": node_metrics.input_total,
            "tasks_succeeded": node_metrics.succeeded,
            "tasks_failed": node_metrics.failed,
            "tasks_skipped": node_metrics.skipped,
            "tasks_processed": node_metrics.processed,
            "tasks_pending": node_metrics.pending,
            "upstream_counts": node_metrics.upstream_counts,
            "downstream_counts": node_metrics.downstream_counts,
        }
        for node, node_metrics in metrics.items()
    }


class PushSnapshotHandler(TickHandler, Observer):
    """把图级指标快照交给推送通道的处理器。

    按拍（:class:`~celestialflow.ticker.core_handler.TickHandler`）从
    :class:`~celestialflow.runtime.util_types.MetricsView` 读取整图指标，经
    :func:`to_status_snapshot` 投影为状态载荷后写入
    :class:`~celestialflow.reporter.core_push.PushInlet`，由推送 spout 异步发送。

    同时作为 :class:`~celestialflow.observer.Observer` 监听图结束事件：快照只在
    节拍上产生，而图收尾会立即停止节拍器，末拍与图结束之间的终态（全部节点
    ``STOPPED`` 与最终计数）不会被任何节拍捕获，因此在 :meth:`on_graph_end` 补推
    一次终态快照。本处理器只做投影与入队，不进行任何网络 IO。
    """

    def __init__(self, metrics_view: MetricsView, inlet: PushInlet) -> None:
        """
        初始化快照推送处理器。

        :param metrics_view: 指标只读视图
        :param inlet: 已绑定推送 spout 的推送 inlet
        """
        self._metrics_view = metrics_view
        self._inlet = inlet

    def on_tick(self, event: TickEvent) -> None:
        """
        读取并推送一次图级状态快照。

        :param event: 当前节拍事件
        """
        self._push_snapshot()

    def on_graph_end(self, event: GraphEndEvent) -> None:
        """
        图结束时补推一次终态快照。

        本回调在节点全部结束、图收尾阶段触发，此时指标已收敛为终值；补推可
        确保服务端拿到图运行结束时的完整状态。

        :param event: 任务图结束事件
        """
        self._push_snapshot()

    def _push_snapshot(self) -> None:
        """读取整图指标并投影入队为一条状态快照记录。"""
        snapshot = to_status_snapshot(self._metrics_view.get_graph_metrics())
        self._inlet.push_snapshot(snapshot)
