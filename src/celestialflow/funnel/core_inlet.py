# funnel/core_inlet.py
from __future__ import annotations

from typing import Any


class BaseInlet:
    """数据收集器基类，负责将记录通过队列发送到对应的监听器。"""

    def __init__(self, queue: Any) -> None:
        """初始化收集器

        :param queue: 记录队列
        """
        self.queue: Any = queue

    def _funnel(self, record: Any) -> None:
        """将记录放入队列

        :param record: 待发送的记录
        """
        self.queue.put(record)
