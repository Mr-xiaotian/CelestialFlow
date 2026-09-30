# reporter/util_types.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from ..observer import ObserverHub


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

    def get_status_snapshot(self) -> dict[str, dict[str, Any]]: ...

    def get_observers(self) -> ObserverHub: ...

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None: ...

    def inject_terminations(self, nodes: Sequence[str]) -> None: ...
