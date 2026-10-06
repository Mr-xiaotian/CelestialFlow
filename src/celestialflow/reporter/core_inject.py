# reporter/core_inject.py
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import requests

from ..observer import ObserverHub, ReporterFailureEvent
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

    每拍 GET ``/api/pull_injection``，把返回的任务与终止符分别交给
    :class:`InjectionTarget` 注入。任务与终止符各自独立注入：任一方注入失败都会以
    ``kind="inject"`` 上报
    :class:`~celestialflow.observer.core_event.ReporterFailureEvent`，但不会阻止
    另一方注入；拉取本身失败则上报 ``kind="pull_tasks"``。

    处理器不持有节拍器，触发节奏由 :attr:`tick_period` 声明：以 1 秒为基准周期时，
    默认每 5 拍（即 5 秒）读取一次。
    """

    tick_period: int = 5

    def __init__(
        self,
        base_url: str,
        graph_id: str,
        target: InjectionTarget,
        observers: ObserverHub,
        session: requests.Session,
    ) -> None:
        """
        初始化注入处理器。

        :param base_url: 远程服务基础地址
        :param graph_id: 上报会话标识，随拉取请求提交给服务端
        :param target: 注入目标，通常是任务图
        :param observers: 图级观察者 hub，用于上报拉取/注入失败
        :param session: 复用的 HTTP 会话，由调用方负责关闭
        """
        self._base_url = base_url
        self._graph_id = graph_id
        self._target = target
        self._observers = observers
        self._session = session

    def on_tick(self, event: TickEvent) -> None:
        """
        拉取一次注入信息并交给注入目标处理。

        :param event: 当前节拍事件
        """
        try:
            res = self._session.get(
                f"{self._base_url}/api/pull_injection",
                params={"graph_id": self._graph_id},
                timeout=_PULL_TIMEOUT,
            )
            if not res.ok:
                raise ReporterError(f"Failed to pull task injection: {res.status_code}")
        except Exception as e:
            self._observers.on_reporter_failure(
                ReporterFailureEvent(kind="pull_tasks", exception=e)
            )
            return

        injection_payload: dict[str, Any] = res.json()
        try:
            self._target.inject_tasks(injection_payload.get("tasks", {}))
        except Exception as e:
            self._observers.on_reporter_failure(
                ReporterFailureEvent(kind="inject", exception=e)
            )
        try:
            self._target.inject_terminations(injection_payload.get("terminations", []))
        except Exception as e:
            self._observers.on_reporter_failure(
                ReporterFailureEvent(kind="inject", exception=e)
            )
