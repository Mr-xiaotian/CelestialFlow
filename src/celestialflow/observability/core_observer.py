# observability/core_observer.py
from __future__ import annotations


class BaseObserver:
    """执行器生命周期观察者基类，子类按需覆写。"""

    def on_start(self, name: str, total: int) -> None: ...

    def on_task_success(self, count: int = 1) -> None: ...

    def on_task_fail(self, count: int = 1) -> None: ...

    def on_task_duplicate(self, count: int = 1) -> None: ...

    def on_tasks_added(self, count: int) -> None: ...

    def on_finish(self) -> None: ...


class CallbackObserver(BaseObserver):
    """通过回调函数创建的轻量观察者，无需定义子类。"""

    def __init__(self, **callbacks):
        for name, fn in callbacks.items():
            setattr(self, name, fn)
