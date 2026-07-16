# stage/__init__.py
"""CelestialFlow 阶段模块。

提供任务执行器（Executor）、节点（Stage）以及拆分器（Splitter）
与路由器（Router）等高级流水线组件。
"""

from .core_executor import TaskExecutor
from .core_stage import TaskStage
from .core_stages import (
    TaskRouter,
    TaskSplitter,
)

__all__ = [
    "TaskExecutor",
    "TaskRouter",
    "TaskSplitter",
    "TaskStage",
]
