import pytest

from celestialflow.funnel.core_inlet import BaseInlet
from celestialflow.funnel.core_spout import BaseSpout
from tests.conftest import wait_until


class MockSpout(BaseSpout):
    def __init__(self):
        """初始化测试用监听器并准备接收列表。"""
        super().__init__()
        self.received = []

    def _handle_record(self, record):
        """记录消费到的输入数据。"""
        self.received.append(record)


class MockInlet(BaseInlet):
    def send(self, data):
        """将数据经由 inlet 发送到目标队列。"""
        self._funnel(data)


class TestBaseInlet:
    def test_inlet_to_spout_communication(self):
        """BaseInlet 通过队列将记录送入监听中的 spout。"""
        spout = MockSpout()
        inlet = MockInlet().bind_spout(spout)

        spout.start()
        try:
            inlet.send('msg1')
            inlet.send({'key': 'val'})
            wait_until(
                lambda: spout.received == ['msg1', {'key': 'val'}]
                and spout.get_pending_count() == 0,
                message='spout did not receive inlet records in time',
            )
        finally:
            spout.stop()

        assert spout.received == ['msg1', {'key': 'val'}]

    def test_funnel_puts_record_into_queue(self):
        """_funnel 应将原始记录直接放入目标队列。"""
        spout = MockSpout()
        inlet = MockInlet().bind_spout(spout)

        inlet.send('queued')

        assert spout.get_queue().get_nowait() == 'queued'
        assert spout.get_pending_count() == 1

    def test_bind_spout_creates_bound_inlet(self):
        """`bind_spout()` 应返回与目标 spout 共享状态的 inlet。"""
        spout = MockSpout()

        inlet = MockInlet().bind_spout(spout)

        assert isinstance(inlet, MockInlet)
        inlet.send("msg")
        assert spout.get_pending_count() == 1
