from __future__ import annotations

from typing import Any, cast

from ..funnel import BaseSpout
from ..runtime import TaskEnvelope


class SuccessSpout[T, R](BaseSpout):
    """
    成功结果监听线程，用于持续读取成功结果队列并缓存 task-result 对
    """

    def __init__(self) -> None:
        """初始化成功结果监听器"""
        super().__init__()
        self.success_pairs: list[tuple[T, R]] = []

    def _before_start(self) -> None:
        """重置成功结果缓存"""
        self.success_pairs = []

    def _handle_record(self, record: Any) -> None:
        """
        处理单条成功结果记录

        :param record: TaskEnvelope 实例，包含结果和原始任务
        """
        if not isinstance(record, TaskEnvelope):
            return

        success_record = cast(TaskEnvelope[R, T], record)
        result = success_record.task
        task = cast(T, success_record.prev)
        self.success_pairs.append((task, result))

    def get_success_pairs(self) -> list[tuple[T, R]]:
        """
        获取成功任务与结果的 pair 列表

        :return: [(task, result), ...]
        """
        return list(self.success_pairs)
