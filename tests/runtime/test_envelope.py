import pytest

from celestialflow.runtime.core_envelope import TaskEnvelope
from celestialflow.runtime.util_hash import object_to_hash


class TestTaskEnvelope:
    def test_create_and_getters(self):
        """测试 TaskEnvelope 的构造函数及其 Getter 方法是否能正确还原原始数据"""
        task = {"key": "value", "num": 42}
        envelope = TaskEnvelope(task, id=100)

        assert envelope.get_task() == task
        assert envelope.get_id() == 100
        assert isinstance(envelope.get_hash(), bytes)
        assert len(envelope.get_hash()) > 0

    def test_change_id(self):
        """测试 change_id 方法能够正确修改信封的 ID"""
        envelope = TaskEnvelope("hello", id=1)
        envelope.id = 999
        assert envelope.get_id() == 999

    def test_different_tasks_different_hash(self):
        """测试不同内容的项目产生不同的哈希值"""
        env1 = TaskEnvelope("task_a", id=1)
        env2 = TaskEnvelope("task_b", id=2)
        assert env1.get_hash() != env2.get_hash()

    def test_same_task_same_hash(self):
        """测试相同内容的项目产生相同的哈希值（即便 ID 不同）"""
        env1 = TaskEnvelope("same", id=1)
        env2 = TaskEnvelope("same", id=2)
        assert env1.get_hash() == env2.get_hash()

    def test_lazy_hash(self):
        """测试哈希值的延迟计算逻辑：只有在首次调用 get_hash 时才计算"""
        envelope = TaskEnvelope("x", id=1)
        assert envelope.hash is None
        envelope.get_hash()
        assert envelope.hash is not None

    def test_unhashable_task_falls_back_to_unique_hash(self):
        """不可 pickle 的任务应回退到仅当前 envelope 唯一的哈希值。"""

        class UnpicklableTask:
            def __getstate__(self):
                raise TypeError("cannot pickle")

        env1 = TaskEnvelope(UnpicklableTask(), id=101)
        env2 = TaskEnvelope(UnpicklableTask(), id=102)

        hash1 = env1.get_hash()
        hash2 = env2.get_hash()

        assert isinstance(hash1, bytes)
        assert isinstance(hash2, bytes)
        assert hash1.startswith(b"__unhashable_task__:")
        assert hash2.startswith(b"__unhashable_task__:")
        assert hash1 != hash2

    def test_slots_memory_efficient(self):
        """测试 __slots__ 限制，确保不能为 TaskEnvelope 实例动态添加非法属性"""
        envelope = TaskEnvelope("x", id=1)
        with pytest.raises(AttributeError):
            envelope.extra_attr = 123


class TestObjectToHash:
    def test_returns_bytes(self):
        """测试 object_to_hash 函数返回的是 bytes 类型"""
        result = object_to_hash(42)
        assert isinstance(result, bytes)

    def test_returns_20_bytes(self):
        """测试 SHA1 哈希结果应固定为 20 字节"""
        assert len(object_to_hash("hello")) == 20

    def test_same_input_same_hash(self):
        """测试相同输入在不同调用中产生一致的哈希结果"""
        assert object_to_hash([1, 2, 3]) == object_to_hash([1, 2, 3])

    def test_different_input_different_hash(self):
        """测试不同输入产生不同的哈希结果"""
        assert object_to_hash("a") != object_to_hash("b")
