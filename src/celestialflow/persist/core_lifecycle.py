# persist/core_lifecycle.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ..funnel import BaseInlet, BaseSpout
from ..observer import (
    Event,
    Observer,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
)
from ..runtime.util_errors import InitializationError
from .util_payload import to_persisted_payload
from .util_sqlite import (
    connect_db,
    insert_record,
    promote_record_to_failed_by_event_id,
    promote_record_to_skipped_by_event_id,
    promote_record_to_success_by_event_id,
    update_retry_by_event_id,
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

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条 lifecycle 记录并写入 sqlite。

        :param record: lifecycle 操作字典
        """
        if self._conn is None:
            raise InitializationError("lifecycle database is not initialized")

        op = str(record["__op__"])
        if op == "insert":
            # 新任务进入某个 node，写入一条 pending 记录。
            changed = insert_record(self._conn, cast(dict[str, Any], record["record"]))
        elif op == "promote_success":
            # 任务成功时，将 pending 记录晋升为 success 并写入结果。
            changed = promote_record_to_success_by_event_id(
                self._conn,
                int(record["event_id"]),
                record["result_json"],
                ts=float(record["ts"]),
            )
        elif op == "promote_failed":
            # 任务最终失败时，将 pending 记录晋升为 failed 并补齐错误信息。
            changed = promote_record_to_failed_by_event_id(
                self._conn,
                int(record["event_id"]),
                int(record["error_id"]),
                ts=float(record["ts"]),
                error_type=str(record["error_type"]),
                error_message=str(record["error_message"]),
            )
        elif op == "update_retry":
            # 任务重试时，更新 pending 记录的重试次数与最近一次错误信息。
            changed = update_retry_by_event_id(
                self._conn,
                int(record["event_id"]),
                ts=float(record["ts"]),
                retry_times=int(record["retry_times"]),
                error_type=str(record["error_type"]),
                error_message=str(record["error_message"]),
            )
        elif op == "promote_skipped":
            # 任务被跳过时，将 pending 记录晋升为 skipped 并切换到跳过事件 ID。
            changed = promote_record_to_skipped_by_event_id(
                self._conn,
                int(record["event_id"]),
                int(record["skip_id"]),
                ts=float(record["ts"]),
            )
        else:
            raise ValueError(f"unsupported lifecycle operation: {op}")
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

    将生命周期操作字典投递到绑定的 spout。记录以 ``__op__`` 区分操作类型，
    其余字段由 :class:`LifecycleSpout` 解释。
    """

    def send(self, record: dict[str, Any]) -> None:
        """
        将一条生命周期记录送入 spout 队列。

        :param record: 生命周期操作字典
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

        - ``TaskInputEvent``：写入一条 pending 记录，表示任务已进入某个 node；
        - ``TaskSuccessEvent``：将 pending 记录晋升为 success 并写入结果；
        - ``TaskFailEvent``：将 pending 记录晋升为 failed，并绑定最终的 error_id；
        - ``TaskSkipEvent``：将 pending 记录晋升为 skipped；
        - ``TaskRetryEvent``：更新 pending 记录的重试次数与最近一次失败信息。

        :param event: 任意观测事件
        """
        match event:
            case TaskInputEvent():
                now = datetime.now()
                pending_item = {
                    "__op__": "insert",
                    "record": {
                        "event_id": event.input_id,
                        "ts": now.timestamp(),
                        "node": event.node,
                        "status": "pending",
                        "task_json": to_persisted_payload(event.task),
                    },
                }
                self._inlet.send(pending_item)
            case TaskSuccessEvent():
                now = datetime.now()
                self._inlet.send(
                    {
                        "__op__": "promote_success",
                        "event_id": event.task_id,
                        "ts": now.timestamp(),
                        "result_json": to_persisted_payload(event.result),
                    }
                )
            case TaskFailEvent():
                now = datetime.now()
                error = event.exception
                fail_item = {
                    "__op__": "promote_failed",
                    "event_id": event.task_id,
                    "error_id": event.error_id,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "ts": now.timestamp(),
                }
                self._inlet.send(fail_item)
            case TaskSkipEvent():
                now = datetime.now()
                self._inlet.send(
                    {
                        "__op__": "promote_skipped",
                        "event_id": event.task_id,
                        "skip_id": event.skip_id,
                        "ts": now.timestamp(),
                    }
                )
            case TaskRetryEvent():
                now = datetime.now()
                error = event.exception
                error_type = type(error).__name__
                error_message = str(error)
                self._inlet.send(
                    {
                        "__op__": "update_retry",
                        "event_id": event.task_id,
                        "retry_times": event.retry_times,
                        "error_type": error_type,
                        "error_message": error_message,
                        "ts": now.timestamp(),
                    }
                )
            case _:
                pass
