# runtime/util_types.py
from enum import IntEnum
from threading import Lock
from multiprocessing import Value as MPValue

from celestialtree import NodeLabelStyle


class TerminationSignal:
    """用于标记任务队列终止的哨兵对象"""

    def __init__(self, _id: int = -1, source: str = "input") -> None:
        self.id = _id
        self.source = source


# 单例 termination signal
TERMINATION_SIGNAL = TerminationSignal()


class TerminationIdPool:
    """终止信号id池，用于存储所有已接收的终止信号"""

    def __init__(self, ids: list[int]) -> None:
        self.ids = ids


class NoOpContext:
    """空上下文管理器，可用于禁用 with 逻辑"""

    def __enter__(self) -> "NoOpContext":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass


class ValueWrapper:
    """线程内/单进程的计数器包装，可选线程锁。"""

    def __init__(self, value: int = 0, lock=None) -> None:
        self.value = value
        self._lock = lock

    def get_lock(self) -> NoOpContext:
        return self._lock or NoOpContext()


class SumCounter:
    """累加多个 counter（ValueWrapper / MPValue）"""

    def __init__(self, mode: str = "serial"):
        self.mode = mode

        if mode == "thread":
            self._lock = Lock()
            self.init_value = ValueWrapper(0, lock=self._lock)
        elif mode == "process":
            self._lock = None
            self.init_value = MPValue("i", 0)
        else:
            self._lock = None
            self.init_value = ValueWrapper(0)

        self.counters: list[ValueWrapper] = []

    def add_init_value(self, value: int) -> None:
        with self.init_value.get_lock():
            self.init_value.value += value

    def append_counter(self, counter: ValueWrapper) -> None:
        self.counters.append(counter)

    def reset(self) -> None:
        # reset 也最好带锁（至少 thread 模式）
        with self.init_value.get_lock():
            self.init_value.value = 0

        for c in self.counters:
            with c.get_lock():
                c.value = 0

    @property
    def value(self) -> int:
        # 读也建议加锁，thread 模式更稳
        with self.init_value.get_lock():
            base = int(self.init_value.value)

        total = base
        for c in self.counters:
            with c.get_lock():
                total += int(c.value)
        return total


class StageStatus(IntEnum):
    NOT_STARTED = 0
    RUNNING = 1
    STOPPED = 2


class NullPrevStage:
    """
    空前置节点，用于表示没有前置节点的情况
    """

    def get_tag(self) -> str:
        return "input"


NULL_PREV_STAGE = NullPrevStage()
STAGE_STYLE = NodeLabelStyle(template="{base}  {payload.name}  ‹{type}›", missing="-")
