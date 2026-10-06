# reporter/core_push.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Literal

import requests

from ..funnel import BaseInlet, BaseSpout
from ..observer import GraphStartEvent, Observer, TaskFailEvent
from ..persist.util_payload import to_persisted_payload
from ..runtime.util_errors import ReporterError

type PushKind = Literal["graph_start", "task_fail"]
"""推送记录类型：``"graph_start"`` 为图元信息，``"task_fail"`` 为任务失败。"""


@dataclass(frozen=True, slots=True)
class PushRecord:
    """
    一条待推送的上报记录。

    ``kind`` 决定推送目标与生效字段：``"graph_start"`` 使用图元信息字段，
    ``"task_fail"`` 使用任务失败字段；与当前 ``kind`` 无关的字段保持默认值。
    """

    kind: PushKind

    # on_graph_start
    graph: str = ""
    graph_mode: str = ""
    start_time: float = 0.0
    class_name: str = ""
    is_dag: bool = False
    nodes: list[str] = field(default_factory=list[str])
    edges: dict[str, list[str]] = field(default_factory=dict[str, list[str]])
    source_nodes: list[str] = field(default_factory=list[str])
    node_meta: dict[str, dict[str, Any]] = field(default_factory=dict[str, dict[str, Any]])

    # on_task_fail
    event_id: int = 0
    node: str = ""
    task_json: Any = None
    error_type: str = ""
    error_message: str = ""
    ts: float = 0.0


class PushSpout(BaseSpout):
    """
    在后台线程中把上报记录推送到远程服务的推送通道。

    每条记录按自身 ``kind`` 分发到对应端点并立即推送；单条推送失败不会中断
    线程（异常被捕获并打印），该条记录会被丢弃。
    """

    def __init__(
        self,
        graph_id: str,
        base_url: str,
        timeout: float = 3.0,
    ) -> None:
        """
        初始化推送监听器。

        :param graph_id: 上报会话标识，随记录一并提交给服务端
        :param base_url: 远程服务基础地址
        :param timeout: 单次推送请求的超时时间（秒），默认 3.0
        """
        super().__init__()
        self.graph_id = graph_id
        self.base_url = base_url
        self.timeout = timeout

        self._session: requests.Session | None = None

    # ==== 生命周期回调 ====

    def _before_start(self) -> None:
        """创建复用的 HTTP 会话。"""
        self._session = requests.Session()

    def _after_stop(self) -> None:
        """关闭 HTTP 会话。"""
        if self._session is not None:
            self._session.close()
            self._session = None

    # ==== 处理 ====

    def _handle_record(self, record: PushRecord) -> None:
        """
        按记录类型推送到对应端点。

        :param record: 队列中取出的记录
        """
        if self._session is None:
            return

        if record.kind == "graph_start":
            res = self._session.post(
                f"{self.base_url}/api/push_graph_meta",
                json={
                    "graph_id": self.graph_id,
                    "graph": record.graph,
                    "graph_mode": record.graph_mode,
                    "start_time": record.start_time,
                    "class_name": record.class_name,
                    "is_dag": record.is_dag,
                    "nodes": record.nodes,
                    "edges": record.edges,
                    "source_nodes": record.source_nodes,
                    "node_meta": record.node_meta,
                },
                timeout=self.timeout,
            )
            if not res.ok:
                raise ReporterError(f"Failed to push graph meta: {res.status_code}")
        elif record.kind == "task_fail":
            res = self._session.post(
                f"{self.base_url}/api/push_error",
                json={
                    "graph_id": self.graph_id,
                    "event_id": record.event_id,
                    "node": record.node,
                    "task_json": record.task_json,
                    "error_type": record.error_type,
                    "error_message": record.error_message,
                    "ts": record.ts,
                },
                timeout=self.timeout,
            )
            if not res.ok:
                raise ReporterError(f"Failed to push error: {res.status_code}")


class NullPushSpout(BaseSpout):
    """空实现的推送监听器，用于关闭上报时的占位对象。

    消费到的记录会被直接丢弃，不建立任何 HTTP 会话，也不上报。
    """

    def _handle_record(self, _record: PushRecord) -> None:
        """
        丢弃记录，不做任何上报。

        :param _record: 队列中取出的记录
        """
        return None


class PushInlet(BaseInlet, Observer):
    """
    推送观察者：把观测到的图启动与任务失败事件转换为上报记录并入队，
    交由推送 spout 发送。
    """

    def on_graph_start(self, event: GraphStartEvent) -> None:
        """
        将图启动事件携带的图元信息转换为上报记录并入队。

        :param event: 任务图启动事件
        """
        self._funnel(PushRecord(
            kind="graph_start",
            graph=event.graph,
            graph_mode=event.graph_mode,
            start_time=event.start_time,
            class_name=event.class_name,
            is_dag=event.is_dag,
            nodes=event.nodes,
            edges=event.edges,
            source_nodes=event.source_nodes,
            node_meta=event.node_meta,
        ))

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        将任务失败事件转换为上报记录并入队。

        :param event: 任务失败事件
        """
        self._funnel(PushRecord(
            kind="task_fail",
            event_id=event.error_id,
            node=event.node,
            task_json=to_persisted_payload(event.task),
            error_type=type(event.exception).__name__,
            error_message=str(event.exception),
            ts=time.time(),
        ))
