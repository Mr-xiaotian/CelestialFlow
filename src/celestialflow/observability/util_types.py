# observability/util_types.py
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Protocol


class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    @property
    def stage_dict(self) -> Mapping[str, ReporterTaskStage]:
        """返回按名称索引的只读节点映射。"""
        ...

    def collect_runtime_snapshot(self) -> None: ...

    def get_graph_id(self) -> str: ...

    def get_lifecycle_path(self) -> Path: ...

    def get_status_snapshot(self) -> dict[str, Any]: ...

    def get_structure_graph(self) -> dict[str, Any]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...


class ReporterTaskStage(Protocol):
    """TaskReporter 依赖的最小任务阶段接口。"""

    def put_task(self, task: Any) -> None: ...

    def put_signal(self) -> None: ...
