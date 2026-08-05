# observability/core_observer.py
from __future__ import annotations

import functools
from typing import Any

_OBSERVER_METHODS = frozenset({
    "on_start",
    "on_task_success",
    "on_task_fail",
    "on_task_duplicate",
    "on_tasks_added",
    "on_finish",
})


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

    # ==== 异常兜底 ====

    def observer_error(self, method_name: str, exception: Exception) -> None:
        """
        观察者回调异常时的兜底处理。

        当任意观察者回调方法抛出异常时，框架会捕获异常并调用此方法。
        子类可覆写此方法以记录错误或计数。

        :param method_name: 抛出异常的方法名称
        :param exception: 捕获的异常
        """
        ...

    # ==== 子类注册 ====

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """
        在子类创建时自动包装覆写的回调方法，使其异常不会逃逸到框架。

        包装器会捕获所有 ``Exception``，调用 :meth:`observer_error` 后返回。
        注意：此方法**不会**包装 ``observer_error`` 自身。

        :param kwargs: 透传给基类的 ``__init_subclass__`` 参数
        """
        super().__init_subclass__(**kwargs)
        for name in _OBSERVER_METHODS:
            original = cls.__dict__.get(name)
            if original is None:
                continue

            @functools.wraps(original)
            def wrapper(
                self: BaseObserver,
                *args: Any,
                _method_name: str = name,
                _original: Any = original,
                **kw: Any,
            ) -> Any:
                try:
                    return _original(self, *args, **kw)
                except Exception as e:
                    self.observer_error(_method_name, e)
                    return None

            setattr(cls, name, wrapper)
