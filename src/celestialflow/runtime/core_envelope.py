# runtime/core_envelope.py
from __future__ import annotations

from .util_hash import object_to_hash


class TaskEnvelope[T]:
    """任务信封，封装原始任务及其哈希、ID 等元信息。"""

    __slots__: tuple[str, ...] = ("_hash", "_hash_computed", "_id", "_task")

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
        self._hash_computed: bool = False
        self._id: int = id

    def get_task(self) -> T:
        """
        获取原始任务

        :return: 原始任务
        """
        return self._task

    def get_hash(self) -> bytes | None:
        """
        获取任务哈希。

        哈希惰性计算并缓存。若任务不可 pickle / hash，则返回 ``None``，
        表示该任务不参与基于内容的去重。

        :return: 任务哈希；任务不可哈希时返回 ``None``
        """
        if self._hash_computed:
            return self._hash

        try:
            self._hash = object_to_hash(self._task)
        except Exception:
            # 不可 pickle / hash 的任务不参与去重，返回 None 由调用方跳过。
            self._hash = None
        self._hash_computed = True
        return self._hash

    def get_id(self) -> int:
        """
        获取任务 ID

        :return: 任务 ID
        """
        return self._id
