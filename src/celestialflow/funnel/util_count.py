from __future__ import annotations

from threading import Lock


class PendingCounter:
    """线程安全的待处理计数器。

    该计数器用于统计某个 spout 对应的记录中，仍未完成处理的数量。
    """

    def __init__(self) -> None:
        """
        初始化计数器。

        :return: ``None``
        """
        self._count = 0
        self._lock = Lock()

    def increment(self) -> int:
        """
        将待处理数量加一。

        :return: 自增后的待处理数量
        :rtype: int
        """
        with self._lock:
            self._count += 1
            return self._count

    def decrement(self) -> int:
        """
        将待处理数量减一。

        :return: 自减后的待处理数量
        :rtype: int
        """
        with self._lock:
            self._count -= 1
            return self._count

    def get_count(self) -> int:
        """
        读取当前待处理数量。

        :return: 当前待处理数量
        :rtype: int
        """
        with self._lock:
            return self._count
