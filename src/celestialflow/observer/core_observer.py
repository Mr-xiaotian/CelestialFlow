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

    # ==== 生命周期 ====

    def start(self) -> None:
        """获取并启动观察者持有的资源。

        默认实现不持有资源，什么都不做。子类可覆写以开启后台线程、打开文件或
        建立连接。

        :class:`~celestialflow.observer.core_hub.ObserverHub` 在其
        :meth:`~celestialflow.observer.core_hub.ObserverHub.start` 中按注册顺序
        调用本方法，因此实现必须是幂等的：重复调用不应重复获取资源。若启动失败，
        应抛出异常且不残留半初始化状态。
        """
        ...

    def stop(self) -> None:
        """释放并关闭观察者持有的资源。

        默认实现不持有资源，什么都不做。子类可覆写以关闭后台线程、文件或连接。

        :class:`~celestialflow.observer.core_hub.ObserverHub` 在其
        :meth:`~celestialflow.observer.core_hub.ObserverHub.stop` 中按注册顺序
        **逆序**调用本方法，因此实现必须是幂等的：重复调用不应报错。
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
