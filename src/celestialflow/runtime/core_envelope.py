# runtime/core_envelope.py
from typing import Any

from .util_hash import object_to_hash


class TaskEnvelope:
    """任务信封，封装原始任务及其哈希、ID、来源等元信息。"""

    __slots__: tuple[str, ...] = ("hash", "id", "prev", "source", "task")

    def __init__(self, task: Any, id: int, source: str, prev: Any = None):
        """
        :param task: 原始任务
        :param id: 任务 ID
        :param source: 任务来源标识
        :param prev: 前一个任务（用于结果缓存时回溯），默认 None
        """
        self.task: Any = task
        self.hash: bytes | None = None
        self.id: int = id

        self.source: str = source
        self.prev: Any = prev

    def get_task(self) -> Any:
        """
        获取原始任务

        :return: 原始任务
        """
        return self.task

    def get_hash(self) -> bytes:
        """
        获取任务哈希

        :return: 任务哈希
        """
        if self.hash is None:
            self.hash = object_to_hash(self.task)
        return self.hash

    def get_id(self) -> int:
        """
        获取任务 ID

        :return: 任务 ID
        """
        return self.id

    def change_id(self, new_id: int) -> None:
        """
        修改 id

        :param new_id: 新的任务 id
        """
        self.id = new_id
