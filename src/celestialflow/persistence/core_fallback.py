# persistence/core_fallback.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ..funnel import BaseInlet, BaseSpout
from ..runtime.util_errors import InitializationError
from .util_payload import to_persisted_payload
from .util_sqlite import (
    connect_db,
    delete_record_by_event_id,
    insert_record,
    load_task_error_records,
    load_task_result_records,
    promote_record_to_failed_by_event_id,
    promote_record_to_success_by_event_id,
    update_record_event_id_by_event_id,
)


class FallbackSpout(BaseSpout):
    """Fallback 记录监听器，将任务生命周期写入 fallback 目录的 sqlite 文件。"""

    def __init__(self, error_source: str) -> None:
        """
        初始化失败记录监听器

        :param error_source: 错误来源标识（用于文件命名）
        """
        super().__init__()

        self.error_source: str = error_source
        self.db_path: Path | None = None

        self._conn: sqlite3.Connection | None = None

    def _before_start(self) -> None:
        """创建 fallback 目录并打开 sqlite 文件。"""
        # 创建 fallback 目录
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.db_path = Path(
            f"./fallback/{date_str}/{self.error_source}({time_str}).sqlite3"
        )
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = connect_db(self.db_path)

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条 fallback 记录并写入 sqlite。

        :param record: fallback 操作字典
        """
        if self._conn is None:
            raise InitializationError("fail database is not initialized")
        op = str(record["__op__"])
        if op == "insert":
            # 新任务进入某个 stage，写入一条 pending 记录。
            changed = insert_record(self._conn, cast(dict[str, Any], record["record"]))
        elif op == "delete":
            # 任务成功或重复时，删除对应的 pending 记录。
            changed = delete_record_by_event_id(self._conn, int(record["event_id"]))
        elif op == "update_event_id":
            # 任务重试时，将 pending 记录迁移到新的 retry 事件 ID。
            changed = update_record_event_id_by_event_id(
                self._conn,
                int(record["event_id"]),
                int(record["new_event_id"]),
                ts=float(record["ts"]),
            )
        elif op == "promote_success":
            # 任务成功时，将 pending 记录晋升为 success 并写入结果。
            changed = promote_record_to_success_by_event_id(
                self._conn,
                int(record["event_id"]),
                record["result"],
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
        else:
            raise ValueError(f"unsupported fallback operation: {op}")
        if changed:
            self._conn.commit()

    def _after_stop(self) -> None:
        """关闭 sqlite 连接，确保剩余事务落盘。"""
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def get_task_error_pairs(self, stage: str) -> list[tuple[Any, tuple[str, str]]]:
        """
        从 sqlite 文件中读取指定 stage 的错误记录

        :param stage: 待读取的 stage 名称
        :return: (task, error_record) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_error_records(str(self.db_path), stage)

    def get_task_result_pairs(self, stage: str) -> list[tuple[Any, Any]]:
        """
        从 sqlite 文件中读取指定 stage 的成功结果记录。

        :param stage: 待读取的 stage 名称
        :return: (task, result) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_result_records(str(self.db_path), stage)


class FallbackInlet(BaseInlet):
    """
    线程安全 fallback 记录包装类，所有生命周期变更通过队列发送到监听线程写入。
    """

    def task_in(self, stage_name: str, event_id: int, task: Any) -> None:
        """
        写入一条 pending 记录，表示任务已进入某个 stage。

        :param stage_name: 阶段唯一名称
        :param event_id: 当前输入事件 ID
        :param task: 任务数据
        """
        now = datetime.now()
        pending_item = {
            "__op__": "insert",
            "record": {
                "event_id": event_id,
                "ts": now.timestamp(),
                "stage": stage_name,
                "status": "pending",
                "task_json": to_persisted_payload(task),
            },
        }
        self._funnel(pending_item)

    def task_success(self, event_id: int, result: Any, persist: bool = False) -> None:
        """
        将已成功处理任务对应的 pending 记录晋升为 success 并写入结果。

        :param event_id: 当前任务事件 ID
        :param result: 任务结果
        :param persist: 是否持久化任务结果，默认 False
        """
        if persist:
            now = datetime.now()
            self._funnel(
                {
                    "__op__": "promote_success",
                    "event_id": event_id,
                    "ts": now.timestamp(),
                    "result": to_persisted_payload(result),
                }
            )
        else:
            self._funnel({"__op__": "delete", "event_id": event_id})

    def task_retry(self, event_id: int, retry_id: int) -> None:
        """
        将 pending 记录迁移到新的 retry 事件 ID。

        :param event_id: 旧事件 ID
        :param retry_id: 新的 retry 事件 ID
        """
        now = datetime.now()
        self._funnel(
            {
                "__op__": "update_event_id",
                "event_id": event_id,
                "new_event_id": retry_id,
                "ts": now.timestamp(),
            }
        )

    def task_duplicate(self, event_id: int) -> None:
        """
        删除已判重任务对应的 pending 记录。

        :param event_id: 当前任务事件 ID
        """
        self._funnel({"__op__": "delete", "event_id": event_id})

    def task_fail(
        self,
        event_id: int,
        error_id: int,
        error: Exception,
    ) -> None:
        """
        将 pending 记录晋升为 failed，并绑定最终的 error_id。

        :param event_id: 当前任务事件 ID
        :param error_id: 最终错误事件 ID
        :param error: 错误信息
        """
        now = datetime.now()
        error_type = type(error).__name__
        error_message = str(error)
        fail_item = {
            "__op__": "promote_failed",
            "event_id": event_id,
            "error_id": error_id,
            "error_type": error_type,
            "error_message": error_message,
            "ts": now.timestamp(),
        }
        self._funnel(fail_item)
