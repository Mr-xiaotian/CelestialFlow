# observer/core_observer_print.py
from threading import Lock

from ..runtime.util_types import ValueWrapper
from .core_event import (
    Event,
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from .core_observer import Observer


class PrintObserver(Observer):
    """基于标准输出的观察者，将任务执行进度通过 ``print`` 输出到控制台。

    所有计数器均为线程安全的 ``ValueWrapper``，在 thread / async 执行模式下可安全调用。

    注意：``total`` 统计所有进入当前节点的任务，包含外部注入与上游下发的任务。
    """

    def __init__(self, name: str) -> None:
        """
        初始化输出观察者，将所有计数器置零

        :param name: 输出前缀，用于区分不同节点的观察者
        """
        lock = Lock()

        self.total: ValueWrapper = ValueWrapper(0, lock)
        self.succeeded: ValueWrapper = ValueWrapper(0, lock)
        self.failed: ValueWrapper = ValueWrapper(0, lock)
        self.skipped: ValueWrapper = ValueWrapper(0, lock)

        self.name: str = name

    def on_event(self, event: Event) -> None:
        """
        接收并处理观测事件，按事件类型更新计数并打印进度。

        节点启动时 ``total`` 已包含启动前注入的任务数。

        :param event: 任意观测事件
        """
        match event:
            case NodeStartEvent():
                print(f"[{self.name}] start total={self.total.get()}")
            case NodeEndEvent():
                print(
                    f"[{self.name}] finish "
                    f"total={self.total.get()}, skipped={self.skipped.get()}, "
                    f"succeeded={self.succeeded.get()}, failed={self.failed.get()}"
                )
            case TaskInputEvent():
                self.total.add(1)
                print(f"[{self.name}] total={self.total.get()}(+1)")
            case TaskSuccessEvent():
                self.succeeded.add(1)
                print(
                    f"[{self.name}] succeeded={self.succeeded.get()}(+1), "
                    f"total={self.total.get()}"
                )
            case TaskFailEvent():
                self.failed.add(1)
                print(
                    f"[{self.name}] failed={self.failed.get()}(+1), "
                    f"total={self.total.get()}"
                )
            case TaskSkipEvent():
                self.skipped.add(1)
                print(
                    f"[{self.name}] skipped={self.skipped.get()}(+1), "
                    f"total={self.total.get()}"
                )
            case _:
                pass
