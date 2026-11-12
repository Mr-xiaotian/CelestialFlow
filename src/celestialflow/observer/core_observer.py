# observer/core_observer.py
from __future__ import annotations

import traceback

from .core_event import Event


class Observer:
    """执行器生命周期观察者基类。

    所有事件统一通过 :meth:`on_event` 进入。实现方继承本基类后只需覆写该方法，
    并使用 ``match`` 按具体事件类型分派处理，未关心的事件类型自然被忽略。

    :class:`~celestialflow.observer.core_hub.ObserverHub` 在转发事件时捕获回调
    抛出的异常，并交由该观察者自身的 :meth:`handle_exception` 处理，不会逃逸到框架
    执行路径。
    """

    def on_event(self, event: Event) -> None:
        """
        观测事件统一回调。

        默认实现忽略所有事件。子类可覆写本方法，并使用 ``match`` 按事件类型分派，
        例如::

            def on_event(self, event: Event) -> None:
                match event:
                    case TaskSuccessEvent():
                        ...
                    case TaskFailEvent():
                        ...

        :param event: 任意观测事件
        """
        ...

    def handle_exception(self, exception: Exception) -> None:
        """
        观察者回调自身抛出异常时的处理回调。

        :class:`~celestialflow.observer.core_hub.ObserverHub` 在转发事件时，
        若本观察者的某个回调抛出异常，会调用本方法进行处理。默认实现将异常
        回溯打印到标准错误；子类可覆写以实现自定义策略（如收集、上报或忽略）。

        若本方法自身也抛出异常，则由 hub 的 ``handle_exception`` 作为最终兜底处理。

        :param exception: 观察者回调抛出的异常
        """
        traceback.print_exception(exception)
