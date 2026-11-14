# reporter/core_inject.py
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Protocol

import requests

from ..runtime.util_errors import InitializationError, ReporterError
from ..ticker import TickEvent, TickHandler

_PULL_TIMEOUT: float = 3.0
"""拉取注入请求的超时时间（秒）。"""


class InjectionTarget(Protocol):
    """注入处理器依赖的最小任务图接口。

    只暴露注入语义，不暴露节点容器与持久化细节，从而让注入处理器与图结构解耦。
    """

    def inject_tasks(self, tasks: Mapping[str, Iterable[Any]]) -> None: ...

    def inject_terminations(self, nodes: Sequence[str]) -> None: ...


class InjectionHandler(TickHandler):
    """按拍从远程服务拉取注入信息并交给任务图处理的节拍处理器。

    每拍 GET ``/api/pull_injection``，把返回的任务与终止符依次交给
    :class:`InjectionTarget` 注入。拉取失败或注入失败都会抛出异常，交由节拍器的
    处理器异常隔离机制处理（默认打印），不影响后续节拍。

    处理器自持 HTTP 会话：在 :meth:`start` 中建立，在 :meth:`stop` 中关闭，
    调用方无需再管理会话。

    处理器不持有节拍器，触发节奏由 :attr:`tick_period` 声明：以 1 秒为基准周期时，
    默认每 5 拍（即 5 秒）读取一次。
    """

    tick_period: int = 5

    def __init__(
        self,
        base_url: str,
        session_id: str,
        target: InjectionTarget,
    ) -> None:
        """
        初始化注入处理器。

        :param base_url: 远程服务基础地址
        :param session_id: 上报会话标识，随拉取请求提交给服务端；
            线上查询参数名为 ``session_id``
        :param target: 注入目标，通常是任务图
        """
        self._base_url = base_url
        self._session_id = session_id
        self._target = target
        self._session: requests.Session | None = None

    # ==== 生命周期 ====

    def start(self) -> None:
        """建立用于拉取注入的 HTTP 会话（幂等）。"""
        if self._session is None:
            self._session = requests.Session()

    def stop(self) -> None:
        """关闭 HTTP 会话（幂等）。"""
        if self._session is not None:
            self._session.close()
            self._session = None

    def on_tick(self, event: TickEvent) -> None:
        """
        拉取一次注入信息并交给注入目标处理。

        :param event: 当前节拍事件
        :raises InitializationError: 处理器尚未 ``start``，会话不存在
        :raises ReporterError: 拉取失败（响应非 2xx）
        """
        session = self._session
        if session is None:
            raise InitializationError("injection session is not initialized")

        res = session.get(
            f"{self._base_url}/api/pull_injection",
            params={"session_id": self._session_id},
            timeout=_PULL_TIMEOUT,
        )
        if not res.ok:
            raise ReporterError(f"Failed to pull task injection: {res.status_code}")

        injection_payload: dict[str, Any] = res.json()
        self._target.inject_tasks(injection_payload.get("tasks", {}))
        self._target.inject_terminations(injection_payload.get("terminations", []))
