import pytest

from celestialflow.funnel.core_inlet import BaseInlet
from celestialflow.funnel.core_spout import BaseSpout
from tests.conftest import wait_until


class MockSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.received = []

    def _handle_record(self, record):
        self.received.append(record)


class MockInlet(BaseInlet):
    def send(self, data):
        self._funnel(data)


class TestBaseInlet:
    def test_inlet_to_spout_communication(self):
        """BaseInlet ????????????? spout?"""
        spout = MockSpout()
        inlet = MockInlet(spout.get_queue())

        spout.start()
        try:
            inlet.send('msg1')
            inlet.send({'key': 'val'})
            wait_until(
                lambda: spout.received == ['msg1', {'key': 'val'}],
                message='spout did not receive inlet records in time',
            )
        finally:
            spout.stop()

        assert spout.received == ['msg1', {'key': 'val'}]

    def test_funnel_puts_record_into_queue(self):
        """_funnel ???????????????"""
        spout = MockSpout()
        inlet = MockInlet(spout.get_queue())

        inlet.send('queued')

        assert spout.get_queue().get_nowait() == 'queued'
