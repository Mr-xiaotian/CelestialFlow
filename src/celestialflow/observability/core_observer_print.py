# observability/core_observer_print.py
from threading import Lock

from ..runtime.util_types import ValueWrapper
from .core_event import (
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

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        节点启动回调，此时 total 已包含启动前注入的任务数

        :param event: 节点启动事件
        """
        print(f"[{self.name}] start total={self.total.get()}")

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        节点结束回调，打印最终统计结果

        :param event: 节点结束事件
        """
        print(
            f"[{self.name}] finish "
            f"total={self.total.get()}, skipped={self.skipped.get()}, "
            f"succeeded={self.succeeded.get()}, failed={self.failed.get()}"
        )

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        任务输入回调

        :param event: 任务输入事件
        """
        self.total.add(1)
        print(f"[{self.name}] total={self.total.get()}(+1)")

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        任务成功回调

        :param event: 任务成功事件
        """
        self.succeeded.add(1)
        print(
            f"[{self.name}] succeeded={self.succeeded.get()}(+1), "
            f"total={self.total.get()}"
        )

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        任务失败回调

        :param event: 任务失败事件
        """
        self.failed.add(1)
        print(f"[{self.name}] failed={self.failed.get()}(+1), total={self.total.get()}")

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        任务跳过回调

        :param event: 任务跳过事件
        """
        self.skipped.add(1)
        print(
            f"[{self.name}] skipped={self.skipped.get()}(+1), total={self.total.get()}"
        )
