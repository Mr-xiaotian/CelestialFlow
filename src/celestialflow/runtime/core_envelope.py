# runtime/core_envelope.py
from __future__ import annotations

from .util_hash import object_to_hash


class TaskEnvelope[T, TPrev]:
    """任务信封，封装原始任务及其哈希、ID、来源等元信息。"""

    __slots__: tuple[str, ...] = ("hash", "id", "prev", "source", "task")

    def __init__(
        self,
        task: T,
        id: int,
        source: str,
        prev: TPrev | None = None,
    ):
        """
        初始化任务信封。

        :param task: 原始任务
        :param id: 任务 ID
        :param source: 任务来源标识
        :param prev: 前一个任务（用于结果缓存时回溯），默认 None
        """
        self.task: T = task
        self.hash: bytes | None = None
        self.id: int = id

        self.source: str = source
        self.prev: TPrev | None = prev

    def get_task(self) -> T:
        """
        获取原始任务

        :return: 原始任务
        """
        return self.task

    def get_hash(self) -> bytes:
        """
        获取任务哈希
        如果任务哈希未计算，则计算并缓存。
        如果任务不可 hash，则退化为仅当前 envelope 唯一的兜底值。

        :return: 任务哈希
        """
        if self.hash is not None:
            return self.hash

        try:
            self.hash = object_to_hash(self.task)
        except Exception:
            # 不可 hash 的任务退化为仅当前 envelope 唯一的兜底值。
            # 使用长度和前缀都区别于 SHA1 的字节串，避免与正常内容哈希冲突。
            self.hash = f"__unhashable_task__:{self.id}".encode("ascii")
        return self.hash

    def get_id(self) -> int:
        """
        获取任务 ID

        :return: 任务 ID
        """
        return self.id

    def get_prev(self) -> TPrev | None:
        """
        获取前一个任务（用于结果缓存时回溯）

        :return: 前一个任务
        """
        return self.prev
