from __future__ import annotations

import threading
from typing import Any, Protocol


class EventClient(Protocol):
    """事件客户端最小抽象接口。"""

    def emit(
        self,
        type_: str,
        parents: list[int] | None = None,
        message: str | None = None,
        payload: list[Any] | dict[str, Any] | None = None,
    ) -> int:
        """发射一个事件并返回对应的事件 ID。"""
        ...


class LocalEventClient:
    """本地事件客户端，只负责生成递增事件 ID。"""

    def __init__(self, start_id: int = 1) -> None:
        """
        初始化本地事件客户端。

        :param start_id: 起始事件 ID，默认 1
        """
        self._next_id = start_id
        self._lock = threading.Lock()

    def emit(
        self,
        type_: str,
        parents: list[int] | None = None,
        message: str | None = None,
        payload: list[Any] | dict[str, Any] | None = None,
    ) -> int:
        """
        发射一个本地事件并返回递增 ID。

        :param type_: 事件类型，当前实现不使用
        :param parents: 父事件 ID 列表，当前实现不使用
        :param message: 事件消息，当前实现不使用
        :param payload: 事件载荷，当前实现不使用
        :return: 递增事件 ID
        """
        _ = type_, parents, message, payload
        with self._lock:
            current_id = self._next_id
            self._next_id += 1
            return current_id


def clone_event_client(client: EventClient) -> EventClient:
    """克隆事件客户端。

    对于本地事件客户端，返回一个新的本地实例；对于其他实现，暂时直接复用。
    """
    if isinstance(client, LocalEventClient):
        return LocalEventClient()
    return client
