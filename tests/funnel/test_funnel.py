import pytest
import time
from celestialflow.funnel.core_inlet import BaseInlet
from celestialflow.funnel.core_spout import BaseSpout
from celestialflow.runtime.util_errors import CelestialFlowError


class MockSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.received = []
        self.before_called = False
        self.after_called = False

    def _before_start(self):
        self.before_called = True

    def _handle_record(self, record):
        self.received.append(record)

    def _after_stop(self):
        self.after_called = True

class MockInlet(BaseInlet):
    def send(self, data):
        self._funnel(data)

class TestFunnelCore:
    def test_base_spout_lifecycle(self):
        """测试 BaseSpout 的生命周期管理：验证启动、停止及钩子函数调用"""
        spout = MockSpout()
        assert not spout.before_called

        spout.start()
        assert spout.before_called

        # 验证 start() 后 spout 正在运行：放入数据应被消费
        spout.get_queue().put("data_before_stop")
        spout.stop()

        assert spout.after_called
        assert "data_before_stop" in spout.received

        # 验证 stop() 后 spout 已停止：再次放入数据不会被消费
        before_count = len(spout.received)
        spout.get_queue().put("data_after_stop")
        time.sleep(0.2)
        assert len(spout.received) == before_count

    def test_inlet_to_spout_communication(self):
        """测试 Inlet 与 Spout 的异步队列通信逻辑"""
        spout = MockSpout()
        inlet = MockInlet(spout.get_queue())

        spout.start()
        try:
            inlet.send("msg1")
            inlet.send({"key": "val"})
            # 给一点时间处理
            time.sleep(0.1)
        finally:
            spout.stop()

        assert spout.received == ["msg1", {"key": "val"}]

    def test_spout_termination_signal(self):
        """测试 stop() 发送终止信号后 spout 正常关闭且不再消费新数据"""
        spout = MockSpout()
        spout.start()

        # 放入测试数据
        spout.get_queue().put("msg1")
        spout.get_queue().put("msg2")

        # 使用公开 API 停止（内部发送 TERMINATION_SIGNAL + join + _after_stop）
        spout.stop()

        # 验证数据在 stop() 前已被消费
        assert spout.received == ["msg1", "msg2"]
        assert spout.after_called

        # 验证 stop() 后不再消费新数据
        before_count = len(spout.received)
        spout.get_queue().put("msg_after_stop")
        time.sleep(0.2)
        assert len(spout.received) == before_count

        # 验证重复调用 stop() 是安全的（幂等）
        spout.stop()

    def test_spout_not_implemented_error(self):
        """测试 BaseSpout 抽象基类：直接调用未实现的方法应报错"""
        base = BaseSpout()
        with pytest.raises(CelestialFlowError, match="_handle_record must be implemented"):
            base._handle_record("anything")
