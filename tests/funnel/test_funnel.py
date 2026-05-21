import pytest
import time
from queue import Queue
from celestialflow.funnel.core_inlet import BaseInlet
from celestialflow.funnel.core_spout import BaseSpout
from celestialflow.runtime.util_types import TerminationSignal

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
        assert spout._thread is not None
        assert spout._thread.is_alive()
        
        spout.stop()
        assert spout.after_called
        assert spout._thread is None

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
        """测试 Spout 接收终止信号后的正常关闭行为"""
        spout = MockSpout()
        spout.start()
        
        # 发送终止信号
        spout.get_queue().put(TerminationSignal(_id=-1, source="test"))
        
        # 等待线程结束（join）
        spout._thread.join(timeout=2)
        assert not spout._thread.is_alive()
        
        # 验证 cleanup 被调用
        spout.stop() # 再次调用 stop 应该是安全的
        assert spout.after_called

    def test_spout_not_implemented_error(self):
        """测试 BaseSpout 抽象基类：直接调用未实现的方法应报错"""
        base = BaseSpout()
        with pytest.raises(NotImplementedError):
            base._handle_record("anything")
