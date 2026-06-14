# runtime/util_types.py
from __future__ import annotations

from dataclasses import dataclass
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


# 单例 termination signal
TERMINATION_SIGNAL = TerminationSignal()


class TerminationIdPool:
    """终止信号id池，用于存储所有已接收的终止信号"""

    ids: list[int]
    id: int
    source: str

    def __init__(self, ids: list[int]) -> None:
        """
        初始化终止信号 ID 池。

        :param ids: 终止信号 ID 列表
        """
        self.ids = ids
        self.id = -1
        self.source = "<signal>"


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
    """线程内/单进程的计数器包装，可选线程锁。"""

    value: int
    _lock: Lock | NoOpContext

    def __init__(self, value: int, lock: Lock | NoOpContext | None = None) -> None:
        """
        初始化值包装器。

        :param value: 初始值
        :param lock: 可选的线程锁，默认 None
        :note: 如果 lock 为 None，则则使用 NoOpContext 作为默认锁
        """
        self.value = value
        self._lock = lock or NoOpContext()

    def get_lock(self) -> Lock | NoOpContext:
        """获取锁对象，无锁时返回空上下文"""
        return self._lock

    def add(self, value: int) -> None:
        """增加值"""
        with self.get_lock():
            self.value += value

    def get(self) -> int:
        """获取当前值"""
        with self.get_lock():
            return self.value

    def reset(self) -> None:
        """重置值为 0"""
        with self.get_lock():
            self.value = 0


class SumCounter:
    """累加多个 counter（ValueWrapper）"""

    lock: Lock | NoOpContext
    init_value: ValueWrapper
    counters: list[ValueWrapper]

    def __init__(self, lock: Lock | NoOpContext | None = None):
        """
        初始化累加计数器。

        :param lock: 可选的线程锁，默认 None
        """
        self.lock = lock or NoOpContext()
        self.init_value = ValueWrapper(value=0, lock=self.lock)
        self.counters = []

    def append_counter(self, counter: ValueWrapper) -> None:
        """
        追加一个外部计数器

        :param counter: 计数器实例（ValueWrapper 或 MPValue）
        """
        self.counters.append(counter)

    def add(self, value: int) -> None:
        """
        增加初始计数值

        :param value: 增加的值
        """
        with self.lock:
            self.init_value.value += value

    def get(self) -> int:
        """获取所有计数器的累加值"""
        with self.lock:
            return self.value

    def reset(self) -> None:
        """重置所有计数器为 0"""
        with self.lock:
            self.init_value.value = 0

        for c in self.counters:
            with c.get_lock():
                c.value = 0

    @property
    def value(self) -> int:
        """计算所有计数器的累加值"""
        # 读不用加锁, 外层已经有锁
        base = int(self.init_value.value)

        total = base
        for c in self.counters:
            with c.get_lock():
                total += int(c.value)
        return total


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
    TASK_DUPLICATE: str = "task.duplicate"
    TERMINATION_INPUT: str = "termination.input"
    TERMINATION_MERGE: str = "termination.merge"


@dataclass(frozen=True)
class PersistedErrorRecord:
    """
    持久化错误记录

    :param error_type: 错误类型名称
    :param error_message: 错误消息
    :param stage: 错误所属节点标签
    :param event_id: 错误事件 ID
    :param timestamp: 错误时间戳字符串
    :param ts: 错误时间戳
    """

    ts: float | None = None
    stage: str = ""
    event_id: int | None = None
    error_type: str = ""
    error_message: str = ""

    def __str__(self) -> str:
        """
        返回错误记录的可读字符串

        :return: 错误展示字符串
        """
        return f"{self.error_type}({self.error_message})"

    def get_group_key(self) -> tuple[str, str]:
        """
        获取错误分组键

        :return: (error_type, error_message)
        """
        return (self.error_type, self.error_message)
