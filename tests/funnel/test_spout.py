import pytest

from celestialflow.funnel.core_inlet import BaseInlet
from celestialflow.funnel.core_spout import BaseSpout
from celestialflow.runtime.util_errors import CelestialFlowError
from tests.conftest import assert_stays_true, wait_until


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


class MockInlet(BaseInlet):
    def send(self, data):
        """将数据经由 inlet 发送到目标队列。"""
        self._funnel(data)


class TestBaseSpout:
    def test_base_spout_lifecycle(self):
        """BaseSpout 启停时应调用生命周期钩子并消费停止前的数据。"""
        spout = MockSpout()
        inlet = MockInlet().bind_spout(spout)
        assert not spout.before_called

        spout.start()
        assert spout.before_called

        inlet.send('data_before_stop')
        wait_until(
            lambda: 'data_before_stop' in spout.received and spout.get_pending_count() == 0,
            message='spout did not finish processing inlet records in time',
        )
        spout.stop()

        assert spout.after_called
        assert 'data_before_stop' in spout.received

        before_count = len(spout.received)
        inlet.send('data_after_stop')
        assert spout.get_pending_count() == 1
        assert_stays_true(
            lambda: len(spout.received) == before_count,
            duration=0.3,
            message='spout consumed records after stop',
        )

    def test_spout_termination_signal(self):
        """`stop()` 发送终止信号后应停止消费且支持重复调用。"""
        spout = MockSpout()
        inlet = MockInlet().bind_spout(spout)
        spout.start()

        inlet.send('msg1')
        inlet.send('msg2')
        spout.stop()

        assert spout.received == ['msg1', 'msg2']
        assert spout.after_called
        assert spout.get_pending_count() == 0

        before_count = len(spout.received)
        inlet.send('msg_after_stop')
        assert spout.get_pending_count() == 1
        assert_stays_true(
            lambda: len(spout.received) == before_count,
            duration=0.3,
            message='spout consumed records after termination stop',
        )

        spout.stop()

    def test_spout_can_restart_after_stop(self):
        """`stop()` 后再次 `start()` 应重新创建后台线程并继续消费。"""
        spout = MockSpout()
        inlet = MockInlet().bind_spout(spout)

        spout.start()
        inlet.send("first")
        wait_until(
            lambda: spout.received == ["first"] and spout.get_pending_count() == 0,
            message="spout did not process first record in time",
        )
        spout.stop()

        spout.start()
        inlet.send("second")
        wait_until(
            lambda: spout.received == ["first", "second"]
            and spout.get_pending_count() == 0,
            message="spout did not process record after restart in time",
        )
        spout.stop()

        assert spout.received == ["first", "second"]

    def test_spout_not_implemented_error(self):
        """未覆写 `_handle_record()` 的 `BaseSpout` 应抛出框架异常。"""
        base = BaseSpout()
        with pytest.raises(CelestialFlowError, match='_handle_record must be implemented'):
            base._handle_record('anything')
