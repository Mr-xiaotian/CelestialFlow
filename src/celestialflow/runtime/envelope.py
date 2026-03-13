from ..runtime.hash import make_hashable, object_to_str_hash


class TaskEnvelope:
    __slots__ = ("task", "hash", "id")

    def __init__(self, task, hash, id):
        self.task = task
        self.hash = hash
        self.id = id

    @classmethod
    def wrap(cls, task, task_id):
        """
        将原始 task 包装为 TaskEnvelope。
        """
        hashable_task = task  # make_hashable(task)
        task_hash = object_to_str_hash(hashable_task)
        task_id = task_id
        return cls(hashable_task, task_hash, task_id)

    def unwrap(self):
        """取出原始 task, 任务哈希, 任务 id（给用户函数用）"""
        return self.task, self.hash, self.id

    def change_id(self, new_id):
        """修改 id"""
        self.id = new_id
