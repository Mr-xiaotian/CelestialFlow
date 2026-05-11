# runtime/util_types.py
from __future__ import annotations

from enum import IntEnum
from threading import Lock
from types import TracebackType

from celestialtree import NodeLabelStyle  # type: ignore[import-unresolved]


class TerminationSignal:
    """用于标记任务队列终止的哨兵对象"""

    def __init__(self, _id: int = -1, source: str = "input") -> None:
        """
        :param _id: 终止信号 ID
        :param source: 信号来源标识
        """
        self.id = _id
        self.source = source


# 单例 termination signal
TERMINATION_SIGNAL = TerminationSignal()


class TerminationIdPool:
    """终止信号id池，用于存储所有已接收的终止信号"""

    def __init__(self, ids: list[int]) -> None:
        """
        :param ids: 终止信号 ID 列表
        """
        self.ids = ids


class NoOpContext:
    """空上下文管理器，可用于禁用 with 逻辑"""

    def __enter__(self) -> "NoOpContext":
        """进入空上下文"""
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        """退出空上下文"""
        pass


class ValueWrapper:
    """线程内/单进程的计数器包装，可选线程锁。"""

    def __init__(self, value: int = 0, lock: Lock | None = None) -> None:
        """
        :param value: 初始值
        :param lock: 可选的线程锁
        """
        self.value = value
        self._lock = lock

    def get_lock(self) -> "Lock | NoOpContext":
        """获取锁对象，无锁时返回空上下文"""
        return self._lock or NoOpContext()


class SumCounter:
    """累加多个 counter（ValueWrapper）"""

    def __init__(self, mode: str = "serial"):
        """
        :param mode: 执行模式，决定锁和计数器实现
        """
        self.mode = mode
        self.init_value: ValueWrapper

        if mode == "thread":
            self.init_value = ValueWrapper(0, lock=Lock())
        else:
            self.init_value = ValueWrapper(0)
        self.counters: list[ValueWrapper] = []

    def add_init_value(self, value: int) -> None:
        """
        增加初始计数值

        :param value: 增加的值
        """
        with self.init_value.get_lock():
            self.init_value.value += value

    def append_counter(self, counter: ValueWrapper) -> None:
        """
        追加一个外部计数器

        :param counter: 计数器实例（ValueWrapper 或 MPValue）
        """
        self.counters.append(counter)

    def reset(self) -> None:
        """重置所有计数器为 0"""
        # reset 也最好带锁（至少 thread 模式）
        with self.init_value.get_lock():
            self.init_value.value = 0

        for c in self.counters:
            with c.get_lock():
                c.value = 0

    @property
    def value(self) -> int:
        """计算所有计数器的累加值"""
        # 读也建议加锁，thread 模式更稳
        with self.init_value.get_lock():
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

    TASK_INPUT = "task.input"
    TASK_SUCCESS = "task.success"
    TASK_ERROR = "task.error"
    TASK_RETRY_PREFIX = "task.retry."
    TASK_DUPLICATE = "task.duplicate"
    TERMINATION_INPUT = "termination.input"
    TERMINATION_MERGE = "termination.merge"


STAGE_STYLE: NodeLabelStyle = NodeLabelStyle(template="{base}  {payload.name}  ‹{type}›", missing="-")  # type: ignore[no-any-unimported]
