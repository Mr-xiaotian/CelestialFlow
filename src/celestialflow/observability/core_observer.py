# observability/core_observer.py
from __future__ import annotations

from collections.abc import Callable
from typing import Any


class BaseObserver:
    """执行器生命周期观察者基类，子类按需覆写。"""

    def on_start(self, name: str, total: int) -> None:
        """
        执行器启动回调

        :param name: 执行器全名
        :param total: 任务总数
        """
        ...

    def on_task_success(self, count: int = 1) -> None:
        """
        任务成功回调

        :param count: 成功任务数量，默认 1
        """
        ...

    def on_task_fail(self, count: int = 1) -> None:
        """
        任务失败回调

        :param count: 失败任务数量，默认 1
        """
        ...

    def on_task_duplicate(self, count: int = 1) -> None:
        """
        重复任务回调

        :param count: 重复任务数量，默认 1
        """
        ...

    def on_tasks_added(self, count: int) -> None:
        """
        新增任务通知

        :param count: 新增任务数量
        """
        ...

    def on_finish(self) -> None:
        """执行器结束回调"""
        ...


class CallbackObserver(BaseObserver):
    """通过回调函数创建的轻量观察者，无需定义子类。"""

    def __init__(self, **callbacks: Callable[..., Any]) -> None:
        """
        通过回调函数创建观察者

        :param callbacks: 以方法名（如 on_finish）为键的回调函数
        """
        for name, fn in callbacks.items():
            setattr(self, name, fn)
