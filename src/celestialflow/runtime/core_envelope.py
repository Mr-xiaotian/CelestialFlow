# runtime/core_envelope.py
from __future__ import annotations

from .util_hash import object_to_hash


class TaskEnvelope[T]:
    """任务信封，封装原始任务及其哈希、ID 等元信息。"""

    __slots__: tuple[str, ...] = ("_hash", "_id", "_task")

    def __init__(
        self,
        task: T,
        id: int,
    ):
        """
        初始化任务信封。

        :param task: 原始任务
        :param id: 任务 ID
        """
        self._task: T = task
        self._hash: bytes | None = None
        self._id: int = id

    def get_task(self) -> T:
        """
        获取原始任务

        :return: 原始任务
        """
        return self._task

    def get_hash(self) -> bytes:
        """
        获取任务哈希
        如果任务哈希未计算，则计算并缓存。
        如果任务不可 hash，则退化为仅当前 envelope 唯一的兜底值。

        :return: 任务哈希
        """
        if self._hash is not None:
            return self._hash

        try:
            self._hash = object_to_hash(self._task)
        except Exception:
            # 不可 hash 的任务退化为仅当前 envelope 唯一的兜底值。
            # 使用长度和前缀都区别于 SHA1 的字节串，避免与正常内容哈希冲突。
            self._hash = f"__unhashable_task__:{self._id}".encode("ascii")
        return self._hash

    def get_id(self) -> int:
        """
        获取任务 ID

        :return: 任务 ID
        """
        return self._id
