# reporter/util_snapshot.py
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..runtime.util_types import NodeMetrics


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
            "end_time": node_metrics.end_time,
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
