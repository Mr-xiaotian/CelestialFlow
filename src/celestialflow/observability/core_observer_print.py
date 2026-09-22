# observability/core_observer_print.py
from threading import Lock

from ..runtime.util_types import ValueWrapper
from .core_observer import BaseObserver


class PrintObserver(BaseObserver):
    """基于日志输出的观察者，将任务执行进度通过 print 输出到控制台"""

    def __init__(self) -> None:
        """初始化日志观察者，将所有计数器置零"""
        lock = Lock()

        self.total: ValueWrapper = ValueWrapper(0, lock)
        self.succeeded: ValueWrapper = ValueWrapper(0, lock)
        self.failed: ValueWrapper = ValueWrapper(0, lock)
        self.duplicated: ValueWrapper = ValueWrapper(0, lock)

    def on_start(self) -> None:
        """
        任务执行器启动时的回调

        :param total: 任务总数
        """
        print(f"[observer] start total={self.total.get()}")

    def on_finish(self) -> None:
        """任务执行器完成后的回调，打印最终统计结果"""
        print(
            "[observer] finish "
            f"total={self.total.get()}, "
            f"succeeded={self.succeeded.get()}, failed={self.failed.get()}, duplicated={self.duplicated.get()}"
        )

    def on_task_added(self, count: int) -> None:
        """
        动态添加新任务时的回调

        :param count: 新增的任务数量
        """
        self.total.add(count)
        print(f"[observer] total={self.total.get()}(+{count})")

    def on_task_success(self, count: int = 1) -> None:
        """
        任务成功执行时的回调

        :param count: 本次成功执行的任务数量，默认 1
        """
        self.succeeded.add(count)
        print(f"[observer] succeeded={self.succeeded.get()}(+{count}), total={self.total.get()}")

    def on_task_fail(self, count: int = 1) -> None:
        """
        任务执行失败时的回调

        :param count: 本次失败的任务数量，默认 1
        """
        self.failed.add(count)
        print(f"[observer] failed={self.failed.get()}(+{count}), total={self.total.get()}")

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        检测到重复任务时的回调

        :param count: 本次去重的任务数量，默认 1
        """
        self.duplicated.add(count)
        print(f"[observer] duplicated={self.duplicated.get()}(+{count}), total={self.total.get()}")
