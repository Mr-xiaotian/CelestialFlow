# runtime/core_envelope.py
from __future__ import annotations


class TaskEnvelope[T]:
    """任务信封，封装原始任务及其 ID 等元信息。"""

    __slots__: tuple[str, ...] = ("_id", "_task")

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
        self._id: int = id

    def get_task(self) -> T:
        """
        获取原始任务

        :return: 原始任务
        """
        return self._task

    def get_id(self) -> int:
        """
        获取任务 ID

        :return: 任务 ID
        """
        return self._id
