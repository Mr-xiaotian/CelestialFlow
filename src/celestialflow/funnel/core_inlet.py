# funnel/core_inlet.py
from __future__ import annotations

from queue import Queue
from typing import TYPE_CHECKING, Any, Self

from ..runtime.util_errors import InitializationError
from .util_count import PendingCounter

if TYPE_CHECKING:
    from .core_spout import BaseSpout


class BaseInlet:
    """数据收集器基类，负责将记录通过队列发送到对应的监听器。"""

    _queue: Queue[Any]
    _counter: PendingCounter

    def bind_spout(self, spout: BaseSpout) -> Self:
        """
        将当前 inlet 绑定到给定 spout。

        :param spout: 目标监听器
        :return: 当前已绑定的 inlet 实例
        :rtype: Self
        """
        self._queue = spout.get_queue()
        self._counter = spout.get_counter()
        return self

    def _funnel(self, record: Any) -> None:
        """
        将记录放入队列。

        :param record: 待发送的记录
        :return: ``None``
        """
        if not hasattr(self, "_queue") or not hasattr(self, "_counter"):
            raise InitializationError("inlet is not bound to spout")

        # 先增加待处理数量，再入队；若入队失败则立即回滚计数。
        self._counter.increment()
        try:
            self._queue.put(record)
        except Exception:
            self._counter.decrement()
            raise
