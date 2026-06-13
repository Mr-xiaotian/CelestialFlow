# persistence/core_fail.py
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Any, cast

from ..funnel import BaseInlet, BaseSpout
from ..runtime.util_errors import InitializationError
from ..runtime.util_types import PersistedErrorRecord
from .util_sqlite import connect_errors_db, insert_error_record, load_task_error_pairs


class FailSpout(BaseSpout):
    """失败记录监听器，将错误信息写入 fallback 目录的 sqlite 文件。"""

    def __init__(self, error_source: str) -> None:
        """
        初始化失败记录监听器

        :param error_source: 错误来源标识（用于文件命名）
        """
        super().__init__()

        self.error_source: str = error_source
        self.db_path: Path | None = None

        self.total_error_num: int = 0
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
        self._conn = connect_errors_db(self.db_path)

        # 初始化计数器
        self.total_error_num = 0
        self._flush_counter = 0

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条错误记录，写入 sqlite 并更新计数器。
        每 _flush_every 条记录才 flush 一次。

        :param record: 错误记录字典
        """
        if self._conn is None:
            raise InitializationError("fail database is not initialized")
        inserted = insert_error_record(self._conn, record)
        if inserted:
            self._flush_counter += 1
            if self._flush_counter >= self._flush_every:
                self._conn.commit()
                self._flush_counter = 0
            self.total_error_num += 1

    def _after_stop(self) -> None:
        """关闭 sqlite 连接，确保剩余事务落盘。"""
        if self._conn:
            self._conn.commit()
            self._conn.close()
            self._conn = None

    def get_error_pairs(self) -> list[tuple[Any, PersistedErrorRecord]]:
        """
        从 sqlite 文件中读取所有错误记录

        :return: (task, error_record) 元组列表
        """
        if self.db_path is None:
            return []
        return load_task_error_pairs(str(self.db_path))


class FailInlet(BaseInlet):
    """
    线程安全失败记录包装类，所有失败记录通过队列发送到监听线程写入
    """

    def __init__(self, fail_queue: Queue[Any]) -> None:
        """
        初始化失败记录收集器

        :param fail_queue: 失败记录队列
        """
        super().__init__(fail_queue)

    def start_graph(self, graph_name: str, structure_graph: dict[str, Any]) -> None:
        """
        在运行开始时写入任务结构元信息到失败持久化流。

        :param structure_graph: 任务图结构 JSON
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "graph_name": graph_name,
            "structure": structure_graph,
        }
        self._funnel(meta_item)

    def start_executor(self, executor_name: str) -> None:
        """
        在运行开始时写入执行器元信息到失败持久化流。

        :param executor_name: 执行器唯一名称
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "executor_name": executor_name,
        }
        self._funnel(meta_item)

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
            "timestamp": now.isoformat(),
            "ts": now.timestamp(),
            "stage": stage_name,
            "error_id": err_id,
            "error_type": error_type,
            "error_message": error_message,
            "task": self._to_retry_payload(task),
        }
        self._funnel(fail_item)
