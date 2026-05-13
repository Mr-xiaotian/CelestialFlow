import pytest

from celestialflow.runtime.core_envelope import TaskEnvelope
from celestialflow.runtime.util_hash import object_to_hash


class TestTaskEnvelope:
    def test_create_and_getters(self):
        """构造与 getter 应还原原始数据"""
        task = {"key": "value", "num": 42}
        envelope = TaskEnvelope(task, id=100, source="test")

        assert envelope.get_task() == task
        assert envelope.get_id() == 100
        assert isinstance(envelope.get_hash(), bytes)
        assert len(envelope.get_hash()) > 0

    def test_source_preserved(self):
        """source 属性应被正确保存"""
        envelope = TaskEnvelope("hello", id=1, source="input")
        assert envelope.source == "input"

    def test_change_id(self):
        """change_id 应修改信封 ID"""
        envelope = TaskEnvelope("hello", id=1, source="input")
        envelope.change_id(999)
        assert envelope.get_id() == 999

    def test_different_tasks_different_hash(self):
        """不同任务应有不同哈希"""
        env1 = TaskEnvelope("task_a", id=1, source="test")
        env2 = TaskEnvelope("task_b", id=2, source="test")
        assert env1.get_hash() != env2.get_hash()

    def test_same_task_same_hash(self):
        """相同任务应有相同哈希"""
        env1 = TaskEnvelope("same", id=1, source="test")
        env2 = TaskEnvelope("same", id=2, source="test")
        assert env1.get_hash() == env2.get_hash()

    def test_lazy_hash(self):
        """hash 应延迟计算"""
        envelope = TaskEnvelope("x", id=1, source="test")
        assert envelope.hash is None
        envelope.get_hash()
        assert envelope.hash is not None

    def test_slots_memory_efficient(self):
        """__slots__ 应阻止动态属性添加"""
        envelope = TaskEnvelope("x", id=1, source="test")
        with pytest.raises(AttributeError):
            envelope.extra_attr = 123  # type: ignore[reportAttributeAccessIssue]


class TestObjectToHash:
    def test_returns_bytes(self):
        """object_to_hash 应返回 bytes 类型"""
        result = object_to_hash(42)
        assert isinstance(result, bytes)

    def test_returns_20_bytes(self):
        """SHA1 digest 应为 20 字节"""
        assert len(object_to_hash("hello")) == 20

    def test_same_input_same_hash(self):
        """相同输入应产生相同哈希"""
        assert object_to_hash([1, 2, 3]) == object_to_hash([1, 2, 3])

    def test_different_input_different_hash(self):
        """不同输入应产生不同哈希"""
        assert object_to_hash("a") != object_to_hash("b")
