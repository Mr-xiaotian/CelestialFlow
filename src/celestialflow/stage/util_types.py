# stage/util_types.py
from typing import Any

from .core_executor import TaskExecutor

type AnyTaskExecutor = TaskExecutor[Any, Any]
