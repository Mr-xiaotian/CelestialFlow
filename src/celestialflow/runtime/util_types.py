# runtime/util_types.py
from __future__ import annotations

from enum import IntEnum
from threading import Lock
from types import TracebackType


class TerminationSignal:
    """用于标记任务队列终止的哨兵对象"""

    id: int
    source: str

    def __init__(self, _id: int = -1, source: str = "input") -> None:
        """
        初始化终止信号。

        :param _id: 终止信号 ID，默认 -1
        :param source: 信号来源标识，默认 "input"
        """
        self.id = _id
        self.source = source


# 单例终止信号
TERMINATION_SIGNAL = TerminationSignal()


class TerminationIdPool:
    """终止信号id池，用于存储所有已接收的终止信号"""

    ids: list[int]

    def __init__(self, ids: list[int]) -> None:
        """
        初始化终止信号 ID 池。

        :param ids: 终止信号 ID 列表
        """
        self.ids = ids


class NoOpContext:
    """空上下文管理器，可用于禁用 with 逻辑"""

    def __enter__(self) -> NoOpContext:
        """进入空上下文"""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """退出空上下文，忽略所有异常信息。

        :param exc_type: 异常类型，未使用
        :param exc_val: 异常值，未使用
        :param exc_tb: 回溯信息，未使用
        """
        pass


class ValueWrapper:
    """线程内/单进程的计数器包装，默认自建线程锁，可显式关闭加锁。"""

    value: int
    _lock: Lock | NoOpContext

    def __init__(self, value: int, lock: Lock | NoOpContext | None = None) -> None:
        """
        初始化值包装器。

        :param value: 初始值
        :param lock: 可选的线程锁，默认 None 表示自建一把锁；
            传入已存在的 Lock 可让多个计数器共用同一把锁；
            显式传入 NoOpContext 则关闭加锁（仅适用于单线程访问）
        """
        self.value = value
        self._lock = lock if lock is not None else Lock()

    def get_lock(self) -> Lock | NoOpContext:
        """获取锁对象，关闭加锁时返回 NoOpContext"""
        return self._lock

    def add(self, value: int) -> None:
        """增加值"""
        with self.get_lock():
            self.value += value

    def get(self) -> int:
        """获取当前值"""
        with self.get_lock():
            return self.value


class StageStatus(IntEnum):
    """Stage 生命周期状态枚举。"""

    NOT_STARTED = 0
    RUNNING = 1
    STOPPED = 2


class CTreeEvent:
    """CelestialTree 事件名称常量"""

    TASK_INPUT: str = "task.input"
    TASK_SUCCESS: str = "task.success"
    TASK_ERROR: str = "task.error"
    TASK_RETRY_PREFIX: str = "task.retry."
    TERMINATION_INPUT: str = "termination.input"
    TERMINATION_MERGE: str = "termination.merge"
