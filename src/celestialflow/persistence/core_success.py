from __future__ import annotations

from typing import Any

from ..funnel import BaseSpout
from ..runtime import TaskEnvelope


class SuccessSpout(BaseSpout):
    """
    成功结果监听线程，用于持续读取成功结果队列并缓存 task-result 对
    """

    def __init__(self) -> None:
        super().__init__()
        self.success_pairs: list[tuple[Any, Any]] = []

    def _before_start(self) -> None:
        self.success_pairs = []

    def _handle_record(self, record: Any) -> None:
        if not isinstance(record, TaskEnvelope):
            return

        result = record.task
        task = record.prev
        self.success_pairs.append((task, result))

    def get_success_pairs(self) -> list[tuple[Any, Any]]:
        """
        获取成功任务与结果的 pair 列表

        :return: [(task, result), ...]
        """
        return list(self.success_pairs)
