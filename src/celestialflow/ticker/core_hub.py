# ticker/core_hub.py
from __future__ import annotations

from threading import Lock

from ..runtime.util_errors import ConfigurationError
from .core_event import TickEvent
from .core_handler import TickHandler, validate_tick_period


class TickHub(TickHandler):
    """节拍分发中心。

    本身即 :class:`~celestialflow.ticker.core_handler.TickHandler`，将每一拍按各
    处理器自身的 :attr:`~celestialflow.ticker.core_handler.TickHandler.tick_period`
    过滤后转发给已注册的处理器。单个处理器回调抛出的异常会被捕获，并交由该处理器
    自身的 :meth:`~celestialflow.ticker.core_handler.TickHandler.handle_exception`
    处理，不会中断其余处理器的分发。若该处理器自身的 ``handle_exception`` 再抛出
    异常，则异常向上传播：当本 hub 由
    :class:`~celestialflow.ticker.core_ticker.Ticker` 驱动时，会被 ticker 捕获并
    回调本 hub 的 :meth:`handle_exception` 兜底。

    处理器列表采用写时复制（copy-on-write）：写入方在 :attr:`_write_lock` 保护下
    用新的不可变元组整体替换 :attr:`_handlers`，读路径 :meth:`_snapshot` 直接返回
    当前引用，不加锁也不拷贝。由于元组不可变、且 CPython 对属性的读取与替换不会
    撕裂，读到的永远是某个完整版本的快照。
    """

    def __init__(self) -> None:
        """初始化分发中心。"""
        self._handlers: tuple[TickHandler, ...] = ()
        self._write_lock = Lock()

    # ==== 注册 ====

    def add_handler(self, handler: TickHandler) -> None:
        """
        注册节拍处理器。

        :param handler: 待注册的处理器
        :raises ConfigurationError: 处理器的 ``tick_period`` 非法，或注册会形成
            循环引用
        """
        validate_tick_period(handler)
        self._reject_cycle(handler)
        with self._write_lock:
            self._handlers = (*self._handlers, handler)

    def _snapshot(self) -> tuple[TickHandler, ...]:
        """
        返回当前处理器元组。

        :return: 当前处理器元组
        """
        return self._handlers

    def _reject_cycle(self, handler: TickHandler) -> None:
        """
        拒绝会形成 hub 循环引用的注册，避免分发时无限递归。

        :param handler: 待注册的处理器
        :raises ConfigurationError: 该处理器已（间接）持有当前 hub
        """
        if handler is self:
            raise ConfigurationError("cannot register a TickHub into itself")
        if not isinstance(handler, TickHub):
            return

        stack: list[TickHub] = [handler]
        seen: set[int] = set()
        while stack:
            hub = stack.pop()
            if id(hub) in seen:
                continue
            seen.add(id(hub))
            if hub is self:
                raise ConfigurationError(
                    "cyclic TickHub registration detected: cannot register a hub "
                    "into a hub that already (directly or transitively) contains it"
                )
            stack.extend(
                child for child in hub._snapshot() if isinstance(child, TickHub)
            )

    # ==== 分发 ====

    def on_tick(self, event: TickEvent) -> None:
        """
        将当前拍转发给所有命中的处理器。

        :param event: 当前节拍事件
        """
        for handler in self._snapshot():
            if not handler.should_tick(event):
                continue
            try:
                handler.on_tick(event)
            except Exception as e:
                handler.handle_exception(e)
