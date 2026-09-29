# persistence/core_lifecycle.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ..funnel import BaseInlet, BaseSpout
from ..observability.core_event import (
    NodeEndEvent,
    NodeStartEvent,
    TaskFailEvent,
    TaskInputEvent,
    TaskRetryEvent,
    TaskSkipEvent,
    TaskSuccessEvent,
    TerminationInputEvent,
    TerminationMergeEvent,
    WorkerCrashEvent,
)
from ..observability.core_observer import Observer
from ..runtime.util_errors import InitializationError
from .util_payload import to_persisted_payload
from .util_sqlite import (
    connect_db,
    insert_record,
    load_task_error_records,
    load_task_result_records,
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

    def get_task_error_pairs(self, node: str) -> list[tuple[Any, tuple[str, str]]]:
        """
        从 sqlite 文件中读取指定 node 的错误记录

        :param node: 待读取的 node 名称
        :return: (task, error_record) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_error_records(str(self.db_path), node)

    def get_task_result_pairs(self, node: str) -> list[tuple[Any, Any]]:
        """
        从 sqlite 文件中读取指定 node 的成功结果记录。

        :param node: 待读取的 node 名称
        :return: (task, result) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_result_records(str(self.db_path), node)


class LifecycleInlet(BaseInlet, Observer):
    """
    线程安全 lifecycle 记录包装类，以观察者形式消费任务事件。

    节点启动/结束事件不产生生命周期记录，因此显式空实现对应回调；
    重试事件仍由执行路径直接调用 :meth:`task_retry`。
    """

    def on_node_start(self, event: NodeStartEvent) -> None:
        """
        节点启动不产生生命周期记录。

        :param event: 节点启动事件
        """

    def on_node_end(self, event: NodeEndEvent) -> None:
        """
        节点结束不产生生命周期记录。

        :param event: 节点结束事件
        """

    def on_termination_input(self, event: TerminationInputEvent) -> None:
        """
        终止信号输入不产生生命周期记录。

        :param event: 终止信号输入事件
        """

    def on_termination_merge(self, event: TerminationMergeEvent) -> None:
        """
        终止信号合并不产生生命周期记录。

        :param event: 终止信号合并事件
        """

    def on_worker_crash(self, event: WorkerCrashEvent) -> None:
        """
        工作器崩溃不产生生命周期记录。

        :param event: 工作器崩溃事件
        """

    def on_task_input(self, event: TaskInputEvent) -> None:
        """
        写入一条 pending 记录，表示任务已进入某个 node。

        :param event: 任务输入事件
        """
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
        self._funnel(pending_item)

    def on_task_success(self, event: TaskSuccessEvent) -> None:
        """
        将已成功处理任务对应的 pending 记录晋升为 success 并写入结果。

        :param event: 任务成功事件
        """
        now = datetime.now()
        self._funnel(
            {
                "__op__": "promote_success",
                "event_id": event.task_id,
                "ts": now.timestamp(),
                "result_json": to_persisted_payload(event.result),
            }
        )

    def on_task_fail(self, event: TaskFailEvent) -> None:
        """
        将 pending 记录晋升为 failed，并绑定最终的 error_id。

        :param event: 任务失败事件
        """
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
        self._funnel(fail_item)

    def on_task_skip(self, event: TaskSkipEvent) -> None:
        """
        将 pending 记录晋升为 skipped，表示任务被跳过而未执行。

        :param event: 任务跳过事件
        """
        now = datetime.now()
        self._funnel(
            {
                "__op__": "promote_skipped",
                "event_id": event.task_id,
                "skip_id": event.skip_id,
                "ts": now.timestamp(),
            }
        )

    def on_task_retry(self, event: TaskRetryEvent) -> None:
        """
        更新 pending 记录的重试次数与最近一次失败的错误信息。

        记录保持 pending 状态，最终由 ``on_task_success`` 或 ``on_task_fail`` 晋升。

        :param event: 任务重试事件
        """
        now = datetime.now()
        error = event.exception
        error_type = type(error).__name__
        error_message = str(error)
        self._funnel(
            {
                "__op__": "update_retry",
                "event_id": event.task_id,
                "retry_times": event.retry_times,
                "error_type": error_type,
                "error_message": error_message,
                "ts": now.timestamp(),
            }
        )
