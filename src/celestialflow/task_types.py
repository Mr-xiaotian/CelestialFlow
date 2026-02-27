from enum import IntEnum
from typing import List
from threading import Lock
from multiprocessing import Value as MPValue

from celestialtree import NodeLabelStyle


class TerminationSignal:
    """用于标记任务队列终止的哨兵对象"""

    def __init__(self, _id: int = -1):
        self.id = _id


# 单例 termination signal
TERMINATION_SIGNAL = TerminationSignal()


class UnconsumedError(Exception):
    """用于标记任务未消费的异常类"""

    pass


class NoOpContext:
    """空上下文管理器，可用于禁用 with 逻辑"""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ValueWrapper:
    """线程内/单进程的计数器包装，可选线程锁。"""

    def __init__(self, value=0, lock=None):
        self.value = value
        self._lock = lock

    def get_lock(self):
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

        self.counters: List[ValueWrapper] = []

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


class TaskEnvelope:
    __slots__ = ("task", "hash", "id")

    def __init__(self, task, hash, id):
        self.task = task
        self.hash = hash
        self.id = id

    @classmethod
    def wrap(cls, task, task_id):
        """
        将原始 task 包装为 TaskEnvelope。
        """
        from .task_tools import make_hashable, object_to_str_hash

        hashable_task = task  # make_hashable(task)
        task_hash = object_to_str_hash(hashable_task)
        task_id = task_id
        return cls(hashable_task, task_hash, task_id)

    def unwrap(self):
        """取出原始 task（给用户函数用）"""
        return self.task

    def change_id(self, new_id):
        """修改 id"""
        self.id = new_id


STAGE_STYLE = NodeLabelStyle(
    template="{base}  {payload.actor_name}  ‹{type}›", missing="-"
)
