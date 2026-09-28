# reporter/util_types.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol


class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。

    只暴露语义能力，不暴露内部节点容器与持久化文件路径，
    从而让 reporter 与图结构、sqlite 表结构解耦。
    """

    def get_graph_id(self) -> str: ...

    def get_nodes(self) -> list[str]: ...

    def get_node_meta(self) -> dict[str, dict[str, Any]]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_nodes(self) -> list[str]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...

    def get_status_snapshot(self) -> dict[str, dict[str, Any]]:
        """采集各节点当前的运行时快照。"""
        ...

    def load_failed_records(self, after_event_id: int | None) -> list[dict[str, Any]]:
        """读取待上报的失败记录；``after_event_id`` 为 ``None`` 时表示全量。"""
        ...

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None:
        """按节点名将注入任务写入待执行队列。"""
        ...

    def inject_terminations(self, nodes: Sequence[str]) -> None:
        """向指定节点注入终止信号。"""
        ...
