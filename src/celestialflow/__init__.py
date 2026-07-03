# __init__.py
"""CelestialFlow — 基于图结构的轻量级异步任务编排框架。

提供任务图构建、执行调度、实时监控、Web 可视化和持久化等核心能力。
"""

from .funnel import BaseInlet, BaseSpout
from .graph import (
    TaskChain,
    TaskComplete,
    TaskCross,
    TaskGraph,
    TaskGrid,
    TaskLoop,
    TaskWheel,
)
from .observability import BaseObserver, TaskProgress
from .persistence.util_sqlite import (
    load_records,
    load_tasks_grouped_by_stage,
)
from .runtime.util_hash import make_hashable
from .runtime.util_types import TerminationSignal
from .stage import (
    TaskExecutor,
    TaskRouter,
    TaskSplitter,
    TaskStage,
)
from .utils.util_benchmark import benchmark_executor, benchmark_graph
from .utils.util_format import format_table
from .web import TaskWebServer

__all__ = [
    "BaseInlet",
    "BaseObserver",
    "BaseSpout",
    "TaskChain",
    "TaskComplete",
    "TaskCross",
    "TaskExecutor",
    "TaskGraph",
    "TaskGrid",
    "TaskLoop",
    "TaskProgress",
    "TaskRouter",
    "TaskSplitter",
    "TaskStage",
    "TaskWebServer",
    "TaskWheel",
    "TerminationSignal",
    "benchmark_executor",
    "benchmark_graph",
    "format_table",
    "load_records",
    "load_tasks_grouped_by_stage",
    "make_hashable",
]
