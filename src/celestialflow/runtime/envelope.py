# runtime/envelope.py
from ..runtime.hash import make_hashable, object_to_str_hash


class TaskEnvelope:
    __slots__ = ("task", "hash", "id", "source")

    def __init__(self, task, hash: str, id: int, source: str = "input"):
        self.task = task
        self.hash = hash
        self.id = id
        self.source = source

    @classmethod
    def wrap(cls, task, task_id: int, source: str = "input"):
        """
        将原始 task 包装为 TaskEnvelope。

        :param task: 原始任务
        :param task_id: 任务 id
        """
        hashable_task = task  # make_hashable(task)
        task_hash = object_to_str_hash(hashable_task)
        task_id = task_id
        return cls(hashable_task, task_hash, task_id, source)

    def unwrap(self):
        """
        解包装 TaskEnvelope
        
        :return: 原始任务, 任务哈希, 任务 id, 任务来源
        """
        return self.task, self.hash, self.id, self.source

    def change_id(self, new_id: int):
        """
        修改 id

        :param new_id: 新的任务 id
        """
        self.id = new_id
