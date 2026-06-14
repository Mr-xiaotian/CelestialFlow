# persistence/core_fallback.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Any, cast

from ..funnel import BaseInlet, BaseSpout
from ..runtime.util_errors import InitializationError
from ..runtime.util_types import PersistedFallbackRecord
from .util_sqlite import connect_db, insert_record, load_task_records


class FallbackSpout(BaseSpout):
    """失败记录监听器，将错误信息写入 fallback 目录的 sqlite 文件。"""

    def __init__(self, error_source: str) -> None:
        """
        初始化失败记录监听器

        :param error_source: 错误来源标识（用于文件命名）
        """
        super().__init__()

        self.error_source: str = error_source
        self.db_path: Path | None = None

        self._conn: sqlite3.Connection | None = None

        # 批量刷新：每 _flush_every 条记录才 flush 一次，避免高频 I/O
        self._flush_every: int = 1
        self._flush_counter: int = 0

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

        # 初始化计数器
        self._flush_counter = 0

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条错误记录，写入 sqlite 并更新计数器。
        每 _flush_every 条记录才 flush 一次。

        :param record: 错误记录字典
        """
        if self._conn is None:
            raise InitializationError("fail database is not initialized")
        inserted = insert_record(self._conn, record)
        if inserted:
            self._flush_counter += 1
            if self._flush_counter >= self._flush_every:
                self._conn.commit()
                self._flush_counter = 0

    def _after_stop(self) -> None:
        """关闭 sqlite 连接，确保剩余事务落盘。"""
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def get_fallback_pairs(self) -> list[tuple[Any, PersistedFallbackRecord]]:
        """
        从 sqlite 文件中读取所有错误记录

        :return: (task, error_record) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_records(str(self.db_path))


class FallbackInlet(BaseInlet):
    """
    线程安全失败记录包装类，所有失败记录通过队列发送到监听线程写入
    """

    def __init__(self, fallback_queue: Queue[Any]) -> None:
        """
        初始化失败记录收集器

        :param fallback_queue: fallback 记录队列
        """
        super().__init__(fallback_queue)

    def _to_retry_payload(self, task: Any) -> Any:
        """
        将失败任务转换为可回填到注入页的 JSON 友好结构。

        :param task: 失败任务
        :return: 可回填到注入页的 JSON 友好结构
        :raises: 任务类型不支持时抛出异常
        """
        if task is None or isinstance(task, str | int | float | bool):
            return task
        if isinstance(task, list | tuple | set):
            iterable_task = cast(list[Any] | tuple[Any, ...] | set[Any], task)
            items = list(iterable_task)
            return [self._to_retry_payload(item) for item in items]
        if isinstance(task, dict):
            task_dict = cast(dict[Any, Any], task)
            return {
                str(key): self._to_retry_payload(value)
                for key, value in task_dict.items()
            }
        return str(task)

    def task_error(
        self,
        stage_name: str,
        err_id: int,
        error: Exception,
        task: Any,
    ) -> None:
        """
        写入错误日志到失败持久化流中。

        :param stage_name: 阶段唯一名称
        :param error: 错误信息
        :param err_id: 错误ID
        :param task: 任务字符串
        """
        now = datetime.now()
        error_type = type(error).__name__
        error_message = str(error)
        fail_item = {
            "event_id": err_id,
            "stage": stage_name,
            "status": "failed",
            "error_type": error_type,
            "error_message": error_message,
            "error_ts": now.timestamp(),
            "task_json": self._to_retry_payload(task),
        }
        self._funnel(fail_item)
