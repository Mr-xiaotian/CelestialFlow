# graph/util_types.py
from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any, Protocol


class ReporterTaskGraph(Protocol):
    """TaskReporter 依赖的最小任务图接口。"""

    def collect_runtime_snapshot(self) -> None: ...

    def put_stage_queue(
        self,
        tasks_dict: Mapping[str, Iterable[Any]],
        put_termination_signal: bool = True,
    ) -> None: ...

    def get_total_error_num(self) -> int: ...

    def get_fallback_path(self) -> str: ...

    def get_status_snapshot(self) -> dict[str, Any]: ...

    def get_structure_graph(self) -> dict[str, Any]: ...

    def get_graph_analysis(self) -> dict[str, Any]: ...
