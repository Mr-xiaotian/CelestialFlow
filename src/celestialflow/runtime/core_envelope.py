# runtime/core_envelope.py
from typing import Any

from .util_hash import object_to_str_hash


class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source", "prev")

    def __init__(self, task: Any, hash: str, id: int, source: str, prev: Any):
        self.task = task
        self.hash = hash
        self.id = id

        self.source = source
        self.prev = prev

    @classmethod
    def wrap(
        cls, task: Any, task_id: int, source: str, prev: Any = None
    ) -> "TaskEnvelope":
        """
        将原始 task 包装为 TaskEnvelope。

        :param task: 原始任务
        :param task_id: 任务 id
        :param source: 任务来源
        :param prev: 前一个任务的 envelope
        """
        task_hash = object_to_str_hash(task)
        return cls(task, task_hash, task_id, source, prev)

    def unwrap(self) -> tuple[Any, str, int]:
        """
        解包装 TaskEnvelope 中的任务信息

        :return: 原始任务, 任务哈希, 任务 id
        """
        return self.task, self.hash, self.id

    def change_id(self, new_id: int) -> None:
        """
        修改 id

        :param new_id: 新的任务 id
        """
        self.id = new_id
