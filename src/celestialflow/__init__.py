# __init__.py
"""CelestialFlow — 基于图结构的轻量级异步任务编排框架。

提供任务图构建、执行调度、实时监控与持久化等核心能力。
"""
from .benchmark.util_benchmark import benchmark_executor, benchmark_graph
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
from .node import (
    TaskExecutor,
    TaskRouter,
    TaskSplitter,
)
from .observer import Observer, ObserverHub, PrintObserver
from .persist.util_sqlite import (
    load_records,
    load_tasks_grouped_by_node,
)
from .reporter import TaskReporter
from .runtime.util_format import format_table
from .runtime.util_types import TerminationSignal
from .ticker import Ticker, TickEvent, TickHandler, TickHub

__all__ = [
    "BaseInlet",
    "BaseSpout",
    "Observer",
    "ObserverHub",
    "PrintObserver",
    "TaskChain",
    "TaskComplete",
    "TaskCross",
    "TaskExecutor",
    "TaskGraph",
    "TaskGrid",
    "TaskLoop",
    "TaskReporter",
    "TaskRouter",
    "TaskSplitter",
    "TaskWheel",
    "TerminationSignal",
    "TickEvent",
    "TickHandler",
    "TickHub",
    "Ticker",
    "benchmark_executor",
    "benchmark_graph",
    "format_table",
    "load_records",
    "load_tasks_grouped_by_node",
]
