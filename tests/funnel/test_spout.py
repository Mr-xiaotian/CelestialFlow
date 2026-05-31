import pytest

from celestialflow.funnel.core_spout import BaseSpout
from celestialflow.runtime.util_errors import CelestialFlowError
from tests.conftest import assert_stays_true


class MockSpout(BaseSpout):
    def __init__(self):
        """初始化测试用监听器状态。"""
        super().__init__()
        self.received = []
        self.before_called = False
        self.after_called = False

    def _before_start(self):
        """标记监听线程即将启动。"""
        self.before_called = True

    def _handle_record(self, record):
        """记录消费到的测试数据。"""
        self.received.append(record)

    def _after_stop(self):
        """标记监听线程已经停止。"""
        self.after_called = True


class TestBaseSpout:
    def test_base_spout_lifecycle(self):
        """BaseSpout 启停时应调用生命周期钩子并消费停止前的数据。"""
        spout = MockSpout()
        assert not spout.before_called

        spout.start()
        assert spout.before_called

        spout.get_queue().put('data_before_stop')
        spout.stop()

        assert spout.after_called
        assert 'data_before_stop' in spout.received

        before_count = len(spout.received)
        spout.get_queue().put('data_after_stop')
        assert_stays_true(
            lambda: len(spout.received) == before_count,
            duration=0.3,
            message='spout consumed records after stop',
        )

    def test_spout_termination_signal(self):
        """`stop()` 发送终止信号后应停止消费且支持重复调用。"""
        spout = MockSpout()
        spout.start()

        spout.get_queue().put('msg1')
        spout.get_queue().put('msg2')
        spout.stop()

        assert spout.received == ['msg1', 'msg2']
        assert spout.after_called

        before_count = len(spout.received)
        spout.get_queue().put('msg_after_stop')
        assert_stays_true(
            lambda: len(spout.received) == before_count,
            duration=0.3,
            message='spout consumed records after termination stop',
        )

        spout.stop()

    def test_spout_not_implemented_error(self):
        """未覆写 `_handle_record()` 的 `BaseSpout` 应抛出框架异常。"""
        base = BaseSpout()
        with pytest.raises(CelestialFlowError, match='_handle_record must be implemented'):
            base._handle_record('anything')
