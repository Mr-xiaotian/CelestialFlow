# observer/core_hub.py
from __future__ import annotations

from threading import Lock

from ..runtime.util_errors import ConfigurationError
from .core_event import Event
from .core_observer import Observer


class ObserverHub(Observer):
    """观察者分发中心。

    本身即 :class:`Observer`，将收到的每个事件按注册顺序转发给已注册的观察者。
    单个观察者回调抛出的异常会被捕获，并交由该观察者自身的
    :meth:`~celestialflow.observer.core_observer.Observer.handle_exception` 处理；
    若该处理器自身再抛出异常，则由本 hub 的 :meth:`handle_exception` 作为最终兜底。
    两种情况下都不会中断其余观察者的分发，也不会逃逸到框架执行路径。

    观察者列表采用写时复制（copy-on-write）：写入方在 :attr:`_write_lock` 保护下
    用新的不可变元组整体替换 :attr:`_observers`，读路径（:meth:`_snapshot`）直接
    返回当前引用，不加锁也不拷贝。由于元组不可变、且 CPython 对属性的读取与替换
    不会撕裂，读到的永远是某个完整版本的快照，迭代期间也无需担心并发修改。
    """

    def __init__(self) -> None:
        """初始化分发中心。"""
        self._observers: tuple[Observer, ...] = ()
        self._write_lock = Lock()

    # ==== 注册 ====

    def add_observer(self, observer: Observer) -> None:
        """
        注册用户观察者。

        :param observer: 待注册的观察者
        :raises ConfigurationError: 注册会形成 hub 循环引用
        """
        self._reject_cycle(observer)
        with self._write_lock:
            self._observers = (*self._observers, observer)

    def _snapshot(self) -> tuple[Observer, ...]:
        """
        返回当前观察者元组。

        元组不可变、且写入方整体替换引用，因此调用方无需加锁即可安全地迭代本次
        事件的一致性快照，读取本身不产生拷贝。

        :return: 当前观察者元组
        """
        return self._observers

    def _reject_cycle(self, observer: Observer) -> None:
        """
        拒绝会形成 hub 循环引用的注册，避免分发时无限递归。

        :param observer: 待注册的观察者
        :raises ConfigurationError: 该观察者已（间接）持有当前 hub
        """
        if observer is self:
            raise ConfigurationError("cannot register an ObserverHub into itself")
        if not isinstance(observer, ObserverHub):
            return

        stack: list[ObserverHub] = [observer]
        seen: set[int] = set()
        while stack:
            hub = stack.pop()
            if id(hub) in seen:
                continue
            seen.add(id(hub))
            if hub is self:
                raise ConfigurationError(
                    "cyclic ObserverHub registration detected: cannot register a hub "
                    "into a hub that already (directly or transitively) contains it"
                )
            stack.extend(
                child for child in hub._snapshot() if isinstance(child, ObserverHub)
            )

    # ==== 查询 ====

    def find[O: Observer](self, observer_type: type[O]) -> O | None:
        """
        查找指定类型的观察者。

        先扫描本层直接注册的观察者，未命中时再按注册顺序递归进入嵌套 hub，
        因此越靠近调用方的注册越优先。匹配使用 :func:`isinstance`，子类实例
        同样会命中。

        :param observer_type: 期望的观察者类型
        :return: 第一个匹配的观察者；未找到时返回 ``None``
        """
        observers = self._snapshot()

        for observer in observers:
            if isinstance(observer, observer_type):
                return observer

        for observer in observers:
            if isinstance(observer, ObserverHub):
                found = observer.find(observer_type)
                if found is not None:
                    return found

        return None

    # ==== 分发 ====

    def on_event(self, event: Event) -> None:
        """
        将事件按注册顺序转发给所有观察者。

        单个观察者回调抛出的异常会被捕获，并交由该观察者自身的
        :meth:`~celestialflow.observer.core_observer.Observer.handle_exception`
        处理；若该处理器自身再抛出异常，则由本 hub 的
        :meth:`~celestialflow.observer.core_observer.Observer.handle_exception`
        作为最终兜底。两种情况都不会中断其余观察者的分发。

        :param event: 待转发的观测事件
        """
        for observer in self._snapshot():
            try:
                observer.on_event(event)
            except Exception as exception:
                try:
                    observer.handle_exception(exception)
                except Exception as fallback:
                    self.handle_exception(fallback)
