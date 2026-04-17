# funnel/core_inlet.py
from __future__ import annotations

from typing import Any


class BaseInlet:
    def __init__(self, queue: Any) -> None:
        self.queue: Any = queue

    def _funnel(self, record: Any) -> None:
        self.queue.put(record)
