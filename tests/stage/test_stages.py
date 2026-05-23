import pytest
from celestialflow.stage.core_stages import TaskSplitter, TaskRouter
from celestialflow.runtime.core_envelope import TaskEnvelope
from celestialflow.runtime.core_queue import TaskOutQueue
from celestialflow.persistence.core_log import LogInlet, LogSpout
from celestialflow.runtime.util_errors import InvalidOptionError, TaskFormatError
from queue import Queue

@pytest.fixture
def log_inlet():
    spout = LogSpout()
    spout.start()
    inlet = LogInlet(spout.get_queue(), log_level="ERROR")
    yield inlet
    spout.stop()

class TestTaskSplitter:
    def test_splitter_init(self):
        """测试 TaskSplitter 的初始配置：应为串行模式且不重试"""
        splitter = TaskSplitter("Splitter")
        assert splitter.execution_mode == "serial"
        assert splitter.max_retries == 0
        assert splitter.unpack_task_args is True
        assert splitter.split_counter.value == 0

    def test_splitter_process_success(self, log_inlet):
        """测试 TaskSplitter 的任务分裂逻辑：成功执行后应生成多个子任务"""
        splitter = TaskSplitter("Splitter")
        # 模拟运行环境
        q = Queue()
        # TaskOutQueue 构造函数要求 queue_list 和 target_names 长度一致
        splitter.result_queue = TaskOutQueue([q], [None], splitter.get_name(), log_inlet)
        splitter.log_inlet = log_inlet

        # 模拟任务执行成功并触发分裂
        # 注意：TaskSplitter._split 只是原样返回，真正分裂逻辑在 process_task_success
        envelope = TaskEnvelope(task=[1, 2, 3], id=1, source="input")
        splitter.process_task_success(envelope, result=[1, 2, 3], start_time=0)

        assert splitter.split_counter.value == 3
        assert q.qsize() == 3
        
        # 验证弹出的内容
        e1 = q.get()
        assert e1.get_task() == 1
        assert e1.source == splitter.get_name()

class TestTaskRouter:
    def test_router_init(self):
        """测试 TaskRouter 的初始配置：应为串行模式且不重试"""
        router = TaskRouter("Router")
        assert router.execution_mode == "serial"
        assert router.max_retries == 0
        assert router.route_counters == {}

    def test_router_route_logic(self):
        """测试 TaskRouter 的核心路由逻辑：正确解析目标名称并提取任务数据"""
        router = TaskRouter("Router")
        # 预注册 target
        router.get_binding_counter("target1")
        
        # 正常路由
        assert router._route(("target1", "data")) == "data"
        
        # 异常路由：未知 target
        with pytest.raises(InvalidOptionError):
            router._route(("unknown", "data"))
            
        # 异常路由：格式错误
        with pytest.raises(TaskFormatError):
            router._route("not_a_tuple") # type: ignore

    def test_router_process_success(self, log_inlet):
        """测试 TaskRouter 的任务分发逻辑：成功执行后应将任务推送到指定目标的队列"""
        router = TaskRouter("Router")
        q_target1 = Queue()
        q_target2 = Queue()
        
        # 注册并绑定计数器（Router 逻辑需要）
        router.get_binding_counter("target1")
        router.get_binding_counter("target2")
        
        # TaskOutQueue 构造函数要求 queue_list 和 target_names 长度一致
        # 我们这里模拟两个具名输出队列
        router.result_queue = TaskOutQueue(
            [q_target1, q_target2], 
            ["target1", "target2"], 
            router.get_name(), 
            log_inlet
        )
        router.log_inlet = log_inlet

        # 路由到 target1
        env1 = TaskEnvelope(task=("target1", "msg1"), id=1, source="input")
        router.process_task_success(env1, result="msg1", start_time=0)
        
        assert router.route_counters["target1"].value == 1
        assert q_target1.qsize() == 1
        assert q_target2.qsize() == 0
        assert q_target1.get().get_task() == "msg1"

        # 路由到 target2
        env2 = TaskEnvelope(task=("target2", "msg2"), id=2, source="input")
        router.process_task_success(env2, result="msg2", start_time=0)
        
        assert router.route_counters["target2"].value == 1
        assert q_target2.qsize() == 1
        assert q_target2.get().get_task() == "msg2"
