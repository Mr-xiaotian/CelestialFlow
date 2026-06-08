# persistence/core_fail.py
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Any, TextIO

from ..funnel import BaseInlet, BaseSpout
from ..runtime.util_errors import InitializationError
from ..runtime.util_types import PersistedErrorRecord
from .util_jsonl import load_task_error_pairs


class FailSpout(BaseSpout):
    """失败记录监听器，将错误信息写入 fallback 目录的 jsonl 文件。"""

    def __init__(self, error_source: str) -> None:
        """
        初始化失败记录监听器

        :param error_source: 错误来源标识（用于文件命名）
        """
        super().__init__()

        self.error_source: str = error_source
        self.jsonl_path: Path | None = None

        self.total_error_num: int = 0
        self._file: TextIO | None = None

        # 批量刷新：每 _flush_every 条记录才 flush 一次，避免高频 I/O
        self._flush_every: int = 1
        self._flush_counter: int = 0

    def _before_start(self) -> None:
        """创建 fallback 目录并打开 jsonl 文件"""
        # 创建 fallback 目录
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.jsonl_path = Path(
            f"./fallback/{date_str}/{self.error_source}({time_str}).jsonl"
        )
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # 打开失败记录文件
        self._file = self.jsonl_path.open("a", encoding="utf-8")

        # 初始化计数器
        self.total_error_num = 0
        self._flush_counter = 0

    def _handle_record(self, record: dict[str, Any]) -> None:
        """
        处理单条错误记录，批量写入 jsonl 文件并更新计数器。
        每 _flush_every 条记录才 flush 一次。

        :param record: 错误记录字典
        """
        jsonl_record: str = json.dumps(record, ensure_ascii=False)

        if self._file is None:
            raise InitializationError("fail file is not initialized")
        _ = self._file.write(f"{jsonl_record}\n")
        self._flush_counter += 1

        if self._flush_counter >= self._flush_every:
            self._file.flush()
            self._flush_counter = 0

        if record.get("error_id") is not None:
            self.total_error_num += 1

    def _after_stop(self) -> None:
        """关闭 jsonl 文件句柄，确保剩余缓冲落盘"""
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None

    def get_error_pairs(self) -> list[tuple[Any, PersistedErrorRecord]]:
        """
        从 jsonl 文件中读取所有错误记录

        :return: (task, error_record) 元组列表
        """
        return load_task_error_pairs(str(self.jsonl_path))


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

    def start_graph(self, structure_graph: dict[str, Any]) -> None:
        """
        在运行开始时写入任务结构元信息到 jsonl 文件

        :param structure_graph: 任务图结构 JSON
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": structure_graph,
        }
        self._funnel(meta_item)

    def start_executor(self, executor_name: str) -> None:
        """
        在运行开始时写入执行器元信息到 jsonl 文件

        :param executor_name: 执行器唯一名称
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "executor": executor_name,
        }
        self._funnel(meta_item)

    def task_error(
        self,
        stage_name: str,
        err_id: int,
        error: Exception,
        task: Any,
    ) -> None:
        """
        写入错误日志到 jsonl 文件中

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
            "task": str(task),
        }
        self._funnel(fail_item)
