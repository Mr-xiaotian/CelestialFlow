# runtime/core_envelope.py
from typing import Any

from .util_hash import object_to_str_hash


class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source")

    def __init__(self, task: Any, hash: str, id: int, source: str = "input"):
        self.task = task
        self.hash = hash
        self.id = id
        self.source = source

    @classmethod
    def wrap(cls, task: Any, task_id: int, source: str = "input") -> "TaskEnvelope":
        """
        将原始 task 包装为 TaskEnvelope。

        :param task: 原始任务
        :param task_id: 任务 id
        :param source: 任务来源
        """
        task_hash = object_to_str_hash(task)
        task_id = task_id
        return cls(task, task_hash, task_id, source)

    def unwrap(self) -> tuple[Any, str, int, str]:
        """
        解包装 TaskEnvelope

        :return: 原始任务, 任务哈希, 任务 id, 任务来源
        """
        return self.task, self.hash, self.id, self.source

    def change_id(self, new_id: int) -> None:
        """
        修改 id

        :param new_id: 新的任务 id
        """
        self.id = new_id
