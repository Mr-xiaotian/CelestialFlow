# observability/core_observer_print.py
from threading import Lock

from ..runtime.util_types import ValueWrapper
from .core_observer import BaseObserver


class PrintObserver(BaseObserver):
    """基于日志输出的观察者，将任务执行进度通过 print 输出到控制台。

    所有计数器均为线程安全的 ``ValueWrapper``，在 thread / async 执行模式下可安全调用。

    注意：``total`` 仅统计经由 ``put_task`` / ``run`` 注入的任务。图模式下由上游节点
    下发的任务不会触发 ``on_task_added``，因此非源节点的 ``total`` 会小于其实际处理量。
    """

    def __init__(self, name: str) -> None:
        """
        初始化日志观察者，将所有计数器置零

        :param name: 输出前缀，用于区分不同节点的观察者
        """
        lock = Lock()

        self.total: ValueWrapper = ValueWrapper(0, lock)
        self.succeeded: ValueWrapper = ValueWrapper(0, lock)
        self.failed: ValueWrapper = ValueWrapper(0, lock)
        self.skipped: ValueWrapper = ValueWrapper(0, lock)

        self.name: str = name

    def on_start(self) -> None:
        """任务执行器启动时的回调，此时 total 已包含启动前注入的任务数"""
        print(f"[{self.name}] start total={self.total.get()}")

    def on_finish(self) -> None:
        """任务执行器完成后的回调，打印最终统计结果"""
        print(
            f"[{self.name}] finish "
            f"total={self.total.get()}, skipped={self.skipped.get()}, "
            f"succeeded={self.succeeded.get()}, failed={self.failed.get()}"
        )

    def on_task_added(self, count: int) -> None:
        """
        动态添加新任务时的回调

        该回调可能先于 ``on_start`` 到达（``run`` 会先注入全部任务再启动执行）。

        :param count: 新增的任务数量
        """
        self.total.add(count)
        print(f"[{self.name}] total={self.total.get()}(+{count})")

    def on_task_success(self, count: int = 1) -> None:
        """
        任务成功执行时的回调

        :param count: 本次成功执行的任务数量，默认 1
        """
        self.succeeded.add(count)
        print(
            f"[{self.name}] succeeded={self.succeeded.get()}(+{count}), total={self.total.get()}"
        )

    def on_task_fail(self, count: int = 1) -> None:
        """
        任务执行失败时的回调

        :param count: 本次失败的任务数量，默认 1
        """
        self.failed.add(count)
        print(
            f"[{self.name}] failed={self.failed.get()}(+{count}), total={self.total.get()}"
        )

    def on_task_skip(self, count: int = 1) -> None:
        """
        任务被跳过时的回调

        :param count: 本次跳过的任务数量，默认 1
        """
        self.skipped.add(count)
        print(
            f"[{self.name}] skipped={self.skipped.get()}(+{count}), total={self.total.get()}"
        )
