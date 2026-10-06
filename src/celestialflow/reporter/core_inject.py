# reporter/core_inject.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import requests

from ..runtime.util_errors import ReporterError
from ..ticker import TickEvent, TickHandler

_PULL_TIMEOUT: float = 3.0
"""拉取注入请求的超时时间（秒）。"""


class InjectionTarget(Protocol):
    """注入处理器依赖的最小任务图接口。

    只暴露注入语义，不暴露节点容器与持久化细节，从而让注入处理器与图结构解耦。
    """

    def inject_tasks(self, tasks: Mapping[str, Sequence[Any]]) -> None: ...

    def inject_terminations(self, nodes: Sequence[str]) -> None: ...


class InjectionHandler(TickHandler):
    """按拍从远程服务拉取注入信息并交给任务图处理的节拍处理器。

    每拍 GET ``/api/pull_injection``，把返回的任务与终止符依次交给
    :class:`InjectionTarget` 注入。拉取失败或注入失败都会抛出异常，交由节拍器的
    处理器异常隔离机制处理（默认打印），不影响后续节拍。

    处理器不持有节拍器，触发节奏由 :attr:`tick_period` 声明：以 1 秒为基准周期时，
    默认每 5 拍（即 5 秒）读取一次。
    """

    tick_period: int = 5

    def __init__(
        self,
        base_url: str,
        graph_id: str,
        target: InjectionTarget,
        session: requests.Session,
    ) -> None:
        """
        初始化注入处理器。

        :param base_url: 远程服务基础地址
        :param graph_id: 上报会话标识，随拉取请求提交给服务端
        :param target: 注入目标，通常是任务图
        :param session: 复用的 HTTP 会话，由调用方负责关闭
        """
        self._base_url = base_url
        self._graph_id = graph_id
        self._target = target
        self._session = session

    def on_tick(self, event: TickEvent) -> None:
        """
        拉取一次注入信息并交给注入目标处理。

        :param event: 当前节拍事件
        """
        res = self._session.get(
            f"{self._base_url}/api/pull_injection",
            params={"graph_id": self._graph_id},
            timeout=_PULL_TIMEOUT,
        )
        if not res.ok:
            raise ReporterError(f"Failed to pull task injection: {res.status_code}")

        injection_payload: dict[str, Any] = res.json()
        self._target.inject_tasks(injection_payload.get("tasks", {}))
        self._target.inject_terminations(injection_payload.get("terminations", []))
