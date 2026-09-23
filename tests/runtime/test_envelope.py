import pytest

from celestialflow.runtime.core_envelope import TaskEnvelope


class TestTaskEnvelope:
    def test_create_and_getters(self):
        """测试 TaskEnvelope 的构造函数及其 Getter 方法是否能正确还原原始数据"""
        task = {"key": "value", "num": 42}
        envelope = TaskEnvelope(task, id=100)

        assert envelope.get_task() == task
        assert envelope.get_id() == 100

    def test_get_id(self):
        """测试 get_id 方法能够正确返回信封的 ID"""
        envelope = TaskEnvelope("hello", id=1)
        assert envelope.get_id() == 1

    def test_slots_memory_efficient(self):
        """测试 __slots__ 限制，确保不能为 TaskEnvelope 实例动态添加非法属性"""
        envelope = TaskEnvelope("x", id=1)
        with pytest.raises(AttributeError):
            envelope.extra_attr = 123
