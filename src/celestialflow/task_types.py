from enum import IntEnum
from typing import List
from multiprocessing import Value as MPValue


class TerminationSignal:
    """用于标记任务队列终止的哨兵对象"""

    pass


# 单例 termination signal
TERMINATION_SIGNAL = TerminationSignal()


class TaskError(Exception):
    """用于标记任务执行错误的异常类"""

    pass


class NoOpContext:
    """空上下文管理器，可用于禁用 with 逻辑"""
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class ValueWrapper:
    """简单包装一个数值，用于进程间共享"""
    def __init__(self, value=0):
        self.value = value


class SumCounter:
    """累加多个 ValueWrapper / MPValue"""
    def __init__(self):
        self.init_value = MPValue("i", 0)
        self.counters: List[ValueWrapper] = []

    def add_init_value(self, value):
        self.init_value.value += value

    def add_counter(self, counter):
        self.counters.append(counter)

    @property
    def value(self):
        return (
            self.init_value.value + sum(c.value for c in self.counters)
            if self.counters
            else self.init_value.value
        )


class StageStatus(IntEnum):
    NOT_STARTED = 0
    RUNNING = 1
    STOPPED = 2
