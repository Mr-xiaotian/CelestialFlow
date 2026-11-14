# reporter/core_push.py
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import requests

from ..funnel import BaseInlet, BaseSpout
from ..observer import Event, GraphEndEvent, GraphStartEvent, Observer, TaskFailEvent
from ..persist.util_payload import to_persisted_payload
from ..runtime.util_errors import ReporterError
from ..runtime.util_types import MetricsView
from .util_snapshot import to_status_snapshot


@dataclass(frozen=True, slots=True)
class GraphStartRecord:
    """任务图元信息推送记录。

    :param graph: 任务图名称
    :param graph_mode: 任务图运行模式
    :param start_time: 任务图启动时间
    :param is_dag: 是否为 DAG 任务图
    :param nodes: 任务图节点名称列表
    :param edges: 任务图边邻接表
    :param source_nodes: 源节点名称列表
    :param node_meta: 各节点的构建期元信息
    """

    graph: str
    graph_mode: str
    start_time: float
    is_dag: bool
    nodes: list[str]
    edges: dict[str, list[str]]
    source_nodes: list[str]
    node_meta: dict[str, dict[str, Any]]


@dataclass(frozen=True, slots=True)
class GraphEndRecord:
    """任务图结束（会话下线）推送记录。

    会话下线通知只需会话标识，该标识由推送 spout 统一附加，故记录本身不携带字段。
    """


@dataclass(frozen=True, slots=True)
class TaskFailRecord:
    """任务失败推送记录。

    :param event_id: 错误事件 ID
    :param node: 节点名称
    :param task_json: 失败任务的 JSON 友好载荷
    :param error_type: 异常类型名称
    :param error_message: 异常消息
    :param ts: 记录时间戳
    """

    event_id: int
    node: str
    task_json: Any
    error_type: str
    error_message: str
    ts: float


@dataclass(frozen=True, slots=True)
class SnapshotRecord:
    """图级状态快照推送记录。

    :param snapshot: 节点名称到状态字典的映射
    """

    snapshot: dict[str, dict[str, Any]]


# 推送记录联合类型，由 PushSpout 按具体类型分发到对应端点。
type PushRecord = GraphStartRecord | GraphEndRecord | TaskFailRecord | SnapshotRecord


class PushSpout(BaseSpout):
    """
    在后台线程中把上报记录推送到远程服务的推送通道。

    每条记录按自身类型分发到对应端点并立即推送；单条推送失败不会中断线程
    （异常被捕获并打印），该条记录会被丢弃。
    """

    def __init__(
        self,
        session_id: str,
        base_url: str,
        timeout: float = 3.0,
    ) -> None:
        """
        初始化推送监听器。

        :param session_id: 上报会话标识，随记录一并提交给服务端；
            线上字段名为 ``session_id``
        :param base_url: 远程服务基础地址
        :param timeout: 单次推送请求的超时时间（秒），默认 3.0
        """
        super().__init__()
        self.session_id = session_id
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

    def _push(self, endpoint: str, payload: dict[str, Any], action: str) -> None:
        """
        向指定端点推送一条记录，失败时抛出 :class:`ReporterError`。

        :param endpoint: 端点路径（以 ``/`` 开头）
        :param payload: JSON 请求体
        :param action: 失败提示中的动作描述
        :raises ReporterError: 响应状态非 2xx 时
        """
        session = self._session
        if session is None:
            return

        res = session.post(
            f"{self.base_url}{endpoint}",
            json=payload,
            timeout=self.timeout,
        )
        if not res.ok:
            raise ReporterError(f"Failed to {action}: {res.status_code}")

    def _handle_record(self, record: PushRecord) -> None:
        """
        按记录类型推送到对应端点。

        :param record: 队列中取出的记录
        """
        match record:
            case GraphStartRecord():
                self._push(
                    "/api/push_graph_meta",
                    {
                        "session_id": self.session_id,
                        "graph": record.graph,
                        "graph_mode": record.graph_mode,
                        "start_time": record.start_time,
                        "is_dag": record.is_dag,
                        "nodes": record.nodes,
                        "edges": record.edges,
                        "source_nodes": record.source_nodes,
                        "node_meta": record.node_meta,
                    },
                    "push graph meta",
                )
            case GraphEndRecord():
                self._push(
                    "/api/shutdown_session",
                    {"session_id": self.session_id},
                    "notify shutdown",
                )
            case TaskFailRecord():
                self._push(
                    "/api/push_error",
                    {
                        "session_id": self.session_id,
                        "event_id": record.event_id,
                        "node": record.node,
                        "task_json": record.task_json,
                        "error_type": record.error_type,
                        "error_message": record.error_message,
                        "ts": record.ts,
                    },
                    "push error",
                )
            case SnapshotRecord():
                self._push(
                    "/api/push_snapshot",
                    {
                        "session_id": self.session_id,
                        "snapshot": record.snapshot,
                        "timestamp": time.time(),
                    },
                    "push snapshot",
                )


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


class PushInlet(BaseInlet):
    """推送记录入口。

    将推送记录投递到绑定的 spout，具体推送目标由 :class:`PushSpout` 按记录类型决定。
    """

    def send(self, record: PushRecord) -> None:
        """
        将一条推送记录送入 spout 队列。

        :param record: 推送记录
        """
        super().send(record)


class PushObserver(Observer):
    """上报推送观察者（门面）。

    将观测事件翻译为推送记录，经 :class:`PushInlet` 投递到后台 :class:`PushSpout`
    异步推送；同时管理 spout 的启停。

    仅处理图级事件与外部的 :meth:`push_snapshot`，其余事件类型在 :meth:`on_event`
    中被忽略。周期状态快照由节拍处理器按拍调用 :meth:`push_snapshot`；图结束时的
    终态快照与会话下线由本观察者在 ``GraphEndEvent`` 中按序补推。
    """

    def __init__(
        self,
        session_id: str,
        base_url: str,
        metrics_view: MetricsView,
        timeout: float = 3.0,
    ) -> None:
        """
        创建并绑定推送 spout 与 inlet。

        :param session_id: 上报会话标识，随记录一并提交给服务端
        :param base_url: 远程服务基础地址
        :param metrics_view: 指标只读视图，用于在图结束时补推终态快照
        :param timeout: 单次推送请求的超时时间（秒），默认 3.0
        """
        self._spout = PushSpout(session_id, base_url, timeout)
        self._inlet = PushInlet().bind_spout(self._spout)
        self._metrics_view = metrics_view

    def start(self) -> None:
        """启动后台推送循环并创建 HTTP 会话。"""
        self._spout.start()

    def stop(self) -> None:
        """停止后台推送循环并关闭 HTTP 会话。"""
        self._spout.stop()

    def on_event(self, event: Event) -> None:
        """
        接收并处理观测事件，按事件类型将对应推送记录入队。

        - ``GraphStartEvent``：图元信息；
        - ``GraphEndEvent``：先入队一次终态快照，再入队会话下线通知。两者在同一
          处理器内连续入队，因此快照一定先于下线被发送；服务端收到下线后把本会话
          标记为已结束，会话数据与错误库仍保留，供前端切换查看；
        - ``TaskFailEvent``：任务失败信息。

        :param event: 任意观测事件
        """
        match event:
            case GraphStartEvent():
                self._inlet.send(
                    GraphStartRecord(
                        graph=event.graph,
                        graph_mode=event.graph_mode,
                        start_time=event.start_time,
                        is_dag=event.is_dag,
                        nodes=event.nodes,
                        edges=event.edges,
                        source_nodes=event.source_nodes,
                        node_meta=event.node_meta,
                    )
                )
            case GraphEndEvent():
                snapshot = to_status_snapshot(self._metrics_view.get_graph_metrics())
                self._inlet.send(SnapshotRecord(snapshot=snapshot))
                self._inlet.send(GraphEndRecord())
            case TaskFailEvent():
                self._inlet.send(
                    TaskFailRecord(
                        event_id=event.error_id,
                        node=event.node,
                        task_json=to_persisted_payload(event.task),
                        error_type=type(event.exception).__name__,
                        error_message=str(event.exception),
                        ts=time.time(),
                    )
                )
            case _:
                pass

    # ==== 供 Ticker 使用 ====

    def push_snapshot(self, snapshot: dict[str, dict[str, Any]]) -> None:
        """
        将图级状态快照转为推送记录并入队。

        该入口不依赖观察者事件，由时间驱动的节拍处理器按拍调用。

        :param snapshot: 节点名称到状态字典的映射
        """
        self._inlet.send(SnapshotRecord(snapshot=snapshot))
