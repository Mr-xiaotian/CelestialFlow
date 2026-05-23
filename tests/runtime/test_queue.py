import queue

import pytest

from celestialflow.runtime.core_envelope import TaskEnvelope
from celestialflow.runtime.core_queue import TaskInQueue, TaskOutQueue
from celestialflow.runtime.util_types import TerminationIdPool, TerminationSignal


class TestTaskInQueue:
    @pytest.fixture
    def simple_queue(self, log_inlet):
        q = queue.Queue()
        return TaskInQueue(q, source_names=[], out_name="test", log_inlet=log_inlet)

    def test_put_and_get_task(self, simple_queue):
        """入队和出队任务信封"""
        envelope = TaskEnvelope("hello", id=1, source="input")
        simple_queue.put(envelope)

        result = simple_queue.get()
        assert isinstance(result, TaskEnvelope)
        assert result.task == "hello"
        assert result.id == 1

    def test_input_termination_direct_exit(self, simple_queue):
        """外部注入的终止信号应直接返回"""
        sig = TerminationSignal(_id=100, source="input")
        simple_queue.put(sig)

        result = simple_queue.get()
        assert isinstance(result, TerminationIdPool)
        assert result.ids == [100]

    def test_multi_source_termination_merge(self, log_inlet):
        """多上游终止信号合并"""
        q = queue.Queue()
        in_queue = TaskInQueue(
            q, source_names=["src_a", "src_b"], out_name="sink", log_inlet=log_inlet
        )

        in_queue.put(TerminationSignal(_id=10, source="src_a"))
        # 此时不应返回，因为 src_b 还没终止
        in_queue.put(TerminationSignal(_id=20, source="src_b"))

        result = in_queue.get()
        assert isinstance(result, TerminationIdPool)
        assert sorted(result.ids) == [10, 20]

    def test_unknown_source_termination_raises(self, simple_queue):
        """未知来源的终止信号应报错"""
        sig = TerminationSignal(_id=99, source="unknown")
        simple_queue.put(sig)
        with pytest.raises(ValueError, match="unknown queue source name"):
            simple_queue.get()

    def test_drain_returns_remaining_tasks(self, log_inlet):
        """drain 应清空队列并返回所有任务"""
        q = queue.Queue()
        in_queue = TaskInQueue(q, source_names=[], out_name="test", log_inlet=log_inlet)

        env1 = TaskEnvelope("a", id=1, source="input")
        env2 = TaskEnvelope("b", id=2, source="input")
        in_queue.put(env1)
        in_queue.put(env2)

        remaining = in_queue.drain()
        assert len(remaining) == 2
        assert remaining[0].task == "a"
        assert remaining[1].task == "b"
        assert q.empty()


class TestTaskOutQueue:
    def test_put_broadcasts_to_all(self, log_inlet):
        """put 应向所有输出队列广播"""
        q1 = queue.Queue()
        q2 = queue.Queue()
        out_queue = TaskOutQueue(
            queue_list=[q1, q2],
            target_names=["a", "b"],
            in_name="src",
            log_inlet=log_inlet,
        )

        envelope = TaskEnvelope("data", id=1, source="src")
        out_queue.put(envelope)

        assert q1.get().task == "data"
        assert q2.get().task == "data"

    def test_put_target_single_queue(self, log_inlet):
        """put_target 只发送到指定队列"""
        q1 = queue.Queue()
        q2 = queue.Queue()
        out_queue = TaskOutQueue(
            queue_list=[q1, q2],
            target_names=["a", "b"],
            in_name="src",
            log_inlet=log_inlet,
        )

        envelope = TaskEnvelope("data", id=1, source="src")
        out_queue.put_target(envelope, name="b")

        assert q1.empty()
        assert q2.get().task == "data"

    def test_add_queue(self, log_inlet):
        """动态添加输出队列"""
        q1 = queue.Queue()
        out_queue = TaskOutQueue(
            queue_list=[q1], target_names=["a"], in_name="src", log_inlet=log_inlet
        )

        q2 = queue.Queue()
        out_queue.add_queue(q2, name="b")

        envelope = TaskEnvelope("x", id=1, source="src")
        out_queue.put(envelope)

        assert q1.get().task == "x"
        assert q2.get().task == "x"

    def test_duplicate_queue_name_raises(self, log_inlet):
        """重复目标名称应报错"""
        q1 = queue.Queue()
        out_queue = TaskOutQueue(
            queue_list=[q1], target_names=["a"], in_name="src", log_inlet=log_inlet
        )
        with pytest.raises(ValueError, match="duplicate queue target name"):
            out_queue.add_queue(queue.Queue(), name="a")
