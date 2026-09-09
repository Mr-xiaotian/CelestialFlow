# node/util_types.py
from typing import Any

from .core_node import BaseTaskNode

type AnyTaskNode = BaseTaskNode[Any, Any]
