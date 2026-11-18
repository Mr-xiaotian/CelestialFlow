# persist/core_lifecycle.py
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from ..funnel import BaseInlet, BaseSpout
from ..observer import (
    Event,
    Observer,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
    TerminationInputEvent,
    TerminationMergeEvent,
)
from ..runtime.util_errors import InitializationError
from ..runtime.util_types import CTreeEvent
from .util_payload import to_persisted_payload
from .util_sqlite import (
    connect_db,
    insert_event,
    insert_event_parents,
    insert_record,
    promote_record_to_failed_by_input_event_id,
    promote_record_to_skipped_by_input_event_id,
    promote_record_to_success_by_input_event_id,
    update_retry_by_input_event_id,
)


@dataclass(frozen=True, slots=True)
class InsertRecord:
    """新任务进入节点时写入的 pending 状态。

    :param input_event_id: 任务输入事件 ID
    :param ts: 记录时间戳
    :param node: 节点名称
    :param task: 任务的 JSON 友好载荷
    """

    input_event_id: int
    ts: float
    node: str
    task: Any
    parent_ids: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class PromoteSuccessRecord:
    """将 pending 状态晋升为 success 并写入任务结果。

    :param input_event_id: 任务输入事件 ID
    :param success_id: 成功事件 ID
    :param ts: 记录时间戳
    :param node: 节点名称
    :param result: 任务结果的 JSON 友好载荷
    """

    input_event_id: int
    success_id: int
    ts: float
    node: str
    result: Any


@dataclass(frozen=True, slots=True)
class PromoteFailedRecord:
    """将 pending 状态晋升为 failed。

    :param input_event_id: 任务输入事件 ID
    :param error_id: 最终失败事件 ID
    :param ts: 记录时间戳
    :param error_type: 异常类型名称
    :param error_message: 异常消息
    """

    input_event_id: int
    error_id: int
    ts: float
    node: str
    error_type: str
    error_message: str


@dataclass(frozen=True, slots=True)
class UpdateRetryRecord:
    """更新 pending 状态的重试次数与最近一次失败信息。

    :param input_event_id: 任务输入事件 ID
    :param retry_id: 重试事件 ID
    :param ts: 记录时间戳
    :param node: 节点名称
    :param retry_times: 已重试次数
    :param error_type: 最近一次异常类型名称
    :param error_message: 最近一次异常消息
    """

    input_event_id: int
    retry_id: int
    ts: float
    node: str
    retry_times: int
    error_type: str
    error_message: str


@dataclass(frozen=True, slots=True)
class PromoteSkippedRecord:
    """将 pending 状态晋升为 skipped。

    :param input_event_id: 任务输入事件 ID
    :param skip_id: 跳过事件 ID
    :param ts: 记录时间戳
    """

    input_event_id: int
    skip_id: int
    ts: float
    node: str


@dataclass(frozen=True, slots=True)
class InsertTerminationInputRecord:
    """写入一条外部终止信号输入事件。"""

    termination_id: int
    ts: float
    node: str


@dataclass(frozen=True, slots=True)
class InsertTerminationMergeRecord:
    """写入一条终止信号合并事件。"""

    termination_id: int
    ts: float
    node: str
    parent_ids: tuple[int, ...]


# 生命周期记录联合类型，由 LifecycleSpout 按具体类型写入 sqlite。
type LifecycleRecord = (
    InsertRecord
    | PromoteSuccessRecord
    | PromoteFailedRecord
    | UpdateRetryRecord
    | PromoteSkippedRecord
    | InsertTerminationInputRecord
    | InsertTerminationMergeRecord
)


class LifecycleSpout(BaseSpout):
    """Lifecycle 记录监听器，将任务生命周期写入 lifecycle 目录的 sqlite 文件。"""

    def __init__(self) -> None:
        """初始化生命周期记录监听器。"""
        super().__init__()

        self.db_path: Path | None = None

        self._conn: sqlite3.Connection | None = None

    def _before_start(self) -> None:
        """创建 lifecycle 目录并打开 sqlite 文件。"""
        # 创建 lifecycle 目录
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.db_path = Path(
            f"./lifecycles/{date_str}/flow_lifecycle({time_str}).sqlite3"
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = connect_db(self.db_path)

    def _handle_record(self, record: LifecycleRecord) -> None:
        """
        处理单条 lifecycle 记录并写入 sqlite。

        :param record: 生命周期记录
        :raises InitializationError: 数据库尚未初始化
        """
        if self._conn is None:
            raise InitializationError("lifecycle database is not initialized")

        changed = False
        match record:
            case InsertRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.input_event_id,
                        "event_type": CTreeEvent.TASK_INPUT,
                        "node": record.node,
                        "ts": record.ts,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.input_event_id,
                    record.parent_ids,
                )
                # 新任务进入某个 node，写入一条 pending 状态。
                changed = (
                    insert_record(
                        self._conn,
                        {
                            "input_event_id": record.input_event_id,
                            "current_event_id": record.input_event_id,
                            "ts": record.ts,
                            "node": record.node,
                            "status": "pending",
                            "task_json": record.task,
                        },
                    )
                    or changed
                )
            case PromoteSuccessRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.success_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TASK_SUCCESS,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.success_id,
                    (record.input_event_id,),
                )
                # 任务成功时，将 pending 状态晋升为 success 并写入结果。
                changed = (
                    promote_record_to_success_by_input_event_id(
                        self._conn,
                        record.input_event_id,
                        record.success_id,
                        record.result,
                        ts=record.ts,
                    )
                    or changed
                )
            case PromoteFailedRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.error_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TASK_ERROR,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.error_id,
                    (record.input_event_id,),
                )
                # 任务最终失败时，将 pending 状态晋升为 failed 并补齐错误信息。
                changed = (
                    promote_record_to_failed_by_input_event_id(
                        self._conn,
                        record.input_event_id,
                        record.error_id,
                        ts=record.ts,
                        error_type=record.error_type,
                        error_message=record.error_message,
                    )
                    or changed
                )
            case UpdateRetryRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.retry_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TASK_RETRY,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.retry_id,
                    (record.input_event_id,),
                )
                # 任务重试时，更新 pending 状态的重试次数与最近一次错误信息。
                changed = (
                    update_retry_by_input_event_id(
                        self._conn,
                        record.input_event_id,
                        record.retry_id,
                        ts=record.ts,
                        retry_times=record.retry_times,
                        error_type=record.error_type,
                        error_message=record.error_message,
                    )
                    or changed
                )
            case PromoteSkippedRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.skip_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TASK_SKIP,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.skip_id,
                    (record.input_event_id,),
                )
                # 任务被跳过时，将 pending 状态晋升为 skipped 并切换到跳过事件 ID。
                changed = (
                    promote_record_to_skipped_by_input_event_id(
                        self._conn,
                        record.input_event_id,
                        record.skip_id,
                        ts=record.ts,
                    )
                    or changed
                )
            case InsertTerminationInputRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.termination_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TERMINATION_INPUT,
                    },
                )
            case InsertTerminationMergeRecord():
                changed = insert_event(
                    self._conn,
                    {
                        "event_id": record.termination_id,
                        "ts": record.ts,
                        "node": record.node,
                        "event_type": CTreeEvent.TERMINATION_MERGE,
                    },
                )
                _ = insert_event_parents(
                    self._conn,
                    record.termination_id,
                    record.parent_ids,
                )
        if changed:
            self._conn.commit()

    def _after_stop(self) -> None:
        """关闭 sqlite 连接，确保剩余事务落盘。"""
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None


class LifecycleInlet(BaseInlet):
    """Lifecycle 记录入口。

    将生命周期记录投递到绑定的 spout，具体写入语义由 :class:`LifecycleSpout`
    按记录类型决定。
    """

    def send(self, record: LifecycleRecord) -> None:
        """
        将一条生命周期记录送入 spout 队列。

        :param record: 生命周期记录
        """
        super().send(record)


class LifecycleObserver(Observer):
    """任务生命周期观察者（门面）。

    将观测事件翻译为生命周期记录，经 :class:`LifecycleInlet` 投递到后台
    :class:`LifecycleSpout` 写入 sqlite；同时管理 spout 的启停并暴露数据库路径。

    仅处理会产生生命周期记录的任务事件，其余事件类型在 :meth:`on_event` 中被忽略。
    """

    def __init__(self) -> None:
        """创建并绑定生命周期 spout 与 inlet。"""
        self._spout = LifecycleSpout()
        self._inlet = LifecycleInlet().bind_spout(self._spout)

    @property
    def db_path(self) -> Path | None:
        """生命周期数据库路径；spout 尚未启动时为 ``None``。"""
        return self._spout.db_path

    def start(self) -> None:
        """启动后台写入循环并创建数据库文件。"""
        self._spout.start()

    def stop(self) -> None:
        """停止后台写入循环并关闭数据库连接。"""
        self._spout.stop()

    def on_event(self, event: Event) -> None:
        """
        接收并处理观测事件，按事件类型写入生命周期记录。

        - ``TaskInputEvent``：写入一条 pending 状态，表示任务已进入某个 node；
        - ``TaskSuccessEvent``：将 pending 状态晋升为 success 并写入结果；
        - ``TaskFailEvent``：将 pending 状态晋升为 failed，并绑定最终的 error_id；
        - ``TaskSkipEvent``：将 pending 状态晋升为 skipped；
        - ``TaskRetryEvent``：更新 pending 状态的重试次数与最近一次失败信息。
        - ``TerminationInputEvent`` / ``TerminationMergeEvent``：仅写入事件账本。

        :param event: 任意观测事件
        """
        match event:
            case TaskInputEvent():
                self._inlet.send(
                    InsertRecord(
                        input_event_id=event.input_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                        task=to_persisted_payload(event.task),
                        parent_ids=event.parent_ids,
                    )
                )
            case TaskSuccessEvent():
                self._inlet.send(
                    PromoteSuccessRecord(
                        input_event_id=event.task_id,
                        success_id=event.success_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                        result=to_persisted_payload(event.result),
                    )
                )
            case TaskFailEvent():
                error = event.exception
                self._inlet.send(
                    PromoteFailedRecord(
                        input_event_id=event.task_id,
                        error_id=event.error_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
            case TaskSkipEvent():
                self._inlet.send(
                    PromoteSkippedRecord(
                        input_event_id=event.task_id,
                        skip_id=event.skip_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                    )
                )
            case TaskRetryEvent():
                error = event.exception
                self._inlet.send(
                    UpdateRetryRecord(
                        input_event_id=event.task_id,
                        retry_id=event.retry_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                        retry_times=event.retry_times,
                        error_type=type(error).__name__,
                        error_message=str(error),
                    )
                )
            case TerminationInputEvent():
                self._inlet.send(
                    InsertTerminationInputRecord(
                        termination_id=event.termination_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                    )
                )
            case TerminationMergeEvent():
                self._inlet.send(
                    InsertTerminationMergeRecord(
                        termination_id=event.termination_id,
                        ts=datetime.now().timestamp(),
                        node=event.node,
                        parent_ids=tuple(event.parent_ids),
                    )
                )
            case _:
                pass
