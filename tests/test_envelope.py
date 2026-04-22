import pytest

from celestialflow.runtime.core_envelope import TaskEnvelope


class TestTaskEnvelope:
    def test_wrap_unwrap(self):
        """包装与解包应还原原始数据"""
        task = {"key": "value", "num": 42}
        envelope = TaskEnvelope.wrap(task, task_id=100, source="test")

        unwrapped_task, task_hash, task_id = envelope.unwrap()
        assert unwrapped_task == task
        assert task_id == 100
        assert isinstance(task_hash, str)
        assert len(task_hash) > 0

    def test_wrap_preserves_source(self):
        """source 属性应被正确保存"""
        envelope = TaskEnvelope.wrap("hello", task_id=1, source="input")
        assert envelope.source == "input"

    def test_change_id(self):
        """change_id 应修改信封 ID"""
        envelope = TaskEnvelope.wrap("hello", task_id=1, source="input")
        envelope.change_id(999)
        assert envelope.id == 999

    def test_different_tasks_different_hash(self):
        """不同任务应有不同哈希"""
        env1 = TaskEnvelope.wrap("task_a", task_id=1, source="test")
        env2 = TaskEnvelope.wrap("task_b", task_id=2, source="test")
        assert env1.hash != env2.hash

    def test_same_task_same_hash(self):
        """相同任务应有相同哈希"""
        env1 = TaskEnvelope.wrap("same", task_id=1, source="test")
        env2 = TaskEnvelope.wrap("same", task_id=2, source="test")
        assert env1.hash == env2.hash

    def test_slots_memory_efficient(self):
        """__slots__ 应阻止动态属性添加"""
        envelope = TaskEnvelope.wrap("x", task_id=1, source="test")
        with pytest.raises(AttributeError):
            envelope.extra_attr = 123
