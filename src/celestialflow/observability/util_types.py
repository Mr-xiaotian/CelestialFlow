# observability/util_types.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def node_dict(self) -> Mapping[str, ReporterTaskExecutor]:
        """返回按名称索引的只读节点映射。"""
        ...

    def get_graph_id(self) -> str: ...

    def get_nodes(self) -> list[str]: ...

    def get_edges(self) -> dict[str, list[str]]: ...

    def get_source_nodes(self) -> list[str]: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...

    def collect_runtime_snapshot(self) -> tuple[dict[str, Any], float]: ...


class ReporterTaskExecutor(Protocol):
    """TaskReporter 依赖的最小执行器接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
