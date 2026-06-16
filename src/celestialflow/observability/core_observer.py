# observability/core_observer.py
from __future__ import annotations


class BaseObserver:
    """执行器生命周期观察者基类，子类按需覆写。"""

    def on_start(self, _name: str, _total: int) -> None:
        """
        执行器启动回调

        :param _name: 执行器全名
        :param _total: 任务总数
        """
        ...

    def on_task_success(self, _count: int = 1) -> None:
        """
        任务成功回调

        :param _count: 成功任务数量，默认 1
        """
        ...

    def on_task_fail(self, _count: int = 1) -> None:
        """
        任务失败回调

        :param _count: 失败任务数量，默认 1
        """
        ...

    def on_task_duplicate(self, _count: int = 1) -> None:
        """
        重复任务回调

        :param _count: 重复任务数量，默认 1
        """
        ...

    def on_tasks_added(self, _count: int) -> None:
        """
        新增任务通知

        :param _count: 新增任务数量
        """
        ...

    def on_finish(self) -> None:
        """执行器结束回调"""
        ...

