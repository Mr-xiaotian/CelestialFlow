# reporter/core_snapshot.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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


class PushSnapshotHandler(TickHandler):
    """按拍把图级指标快照交给推送通道的节拍处理器。

    每拍从 :class:`~celestialflow.runtime.util_types.MetricsView` 读取整图指标，
    经 :func:`to_status_snapshot` 投影为状态载荷后写入
    :class:`~celestialflow.reporter.core_push.PushInlet`，由推送 spout 异步发送。
    本处理器只做投影与入队，不进行任何网络 IO。
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
        snapshot = to_status_snapshot(self._metrics_view.get_graph_metrics())
        self._inlet.push_snapshot(snapshot)
