import pytest

from celestialflow.runtime.core_metrics import TaskMetrics
from celestialflow.runtime.util_types import ValueWrapper


class TestTaskMetricsBasic:
    def test_initial_counts(self):
        """测试 TaskMetrics 的初始计数器状态：所有指标应默认为 0"""
        metrics = TaskMetrics()
        counts = metrics.get_counts()
        assert counts["tasks_input"] == 0
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 0
        assert counts["tasks_duplicated"] == 0
        assert counts["tasks_processed"] == 0
        assert counts["tasks_pending"] == 0
        assert metrics.get_upstream_counts() == {}
        assert metrics.get_downstream_counts() == {}

    def test_add_task_count(self):
        """测试任务总数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_task_count(5)
        assert metrics.get_task_count() == 5
        assert metrics.get_counts()["tasks_input"] == 5

    def test_add_success_count(self):
        """测试任务成功计数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_success_count(3)
        assert metrics.get_success_count() == 3
        assert metrics.get_counts()["tasks_succeeded"] == 3

    def test_add_fail_count(self):
        """测试任务失败计数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_fail_count(2)
        assert metrics.get_fail_count() == 2
        assert metrics.get_counts()["tasks_failed"] == 2

    def test_add_duplicate_count(self):
        """测试重复任务计数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_duplicate_count(4)
        assert metrics.get_duplicate_count() == 4
        assert metrics.get_counts()["tasks_duplicated"] == 4

    def test_processed_equals_sum(self):
        """测试已处理任务数的计算公式：Processed = Success + Failed + Duplicate"""
        metrics = TaskMetrics()
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.add_fail_count(2)
        metrics.add_duplicate_count(1)

        counts = metrics.get_counts()
        assert counts["tasks_processed"] == 8
        assert counts["tasks_pending"] == 2

    def test_is_tasks_finished_true(self):
        """测试任务完成状态判定：当已处理数等于总数时应返回 True"""
        metrics = TaskMetrics()
        metrics.add_task_count(3)
        metrics.add_success_count(2)
        metrics.add_fail_count(1)
        assert metrics.is_tasks_finished() is True

    def test_is_tasks_finished_false(self):
        """测试任务完成状态判定：仍有未处理任务（Pending > 0）时应返回 False"""
        metrics = TaskMetrics()
        metrics.add_task_count(5)
        metrics.add_success_count(2)
        assert metrics.is_tasks_finished() is False

    def test_reset_counter(self):
        """测试计数器重置功能：所有累加指标应归零"""
        metrics = TaskMetrics()
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.reset_counter()
        assert metrics.get_task_count() == 0
        assert metrics.get_success_count() == 0

class TestTaskMetricsBinding:
    """覆盖上游/下游绑定计数器（``connect_to`` 建立的计数关联）。"""

    def test_upstream_counter_adds_to_task_count(self):
        """上游计数器的值应计入任务总数。"""
        metrics = TaskMetrics()
        upstream = ValueWrapper(0)
        metrics.set_upstream_counter("prev", upstream)

        upstream.add(3)

        assert metrics.get_task_count() == 3

    def test_shared_binding_counter(self):
        """``connect_to`` 双方应共享同一个计数器对象。"""
        prev_metrics = TaskMetrics()
        curr_metrics = TaskMetrics()
        counter = ValueWrapper(value=0)
        prev_metrics.set_downstream_counter("current", counter)
        curr_metrics.set_upstream_counter("prev", counter)

        prev_metrics.add_downstream_count("current", 2)

        assert curr_metrics.get_task_count() == 2

    def test_add_downstream_count_missing_target_raises(self):
        """未注册的下游名称应抛出 ``KeyError``。"""
        metrics = TaskMetrics()
        with pytest.raises(KeyError):
            metrics.add_downstream_count("ghost")

    def test_reset_counter_clears_binding_counters(self):
        """``reset_counter`` 应重置上游/下游绑定计数器。"""
        prev_metrics = TaskMetrics()
        curr_metrics = TaskMetrics()
        counter = ValueWrapper(value=0)
        prev_metrics.set_downstream_counter("current", counter)
        curr_metrics.set_upstream_counter("prev", counter)

        prev_metrics.add_downstream_count("current", 5)
        curr_metrics.reset_counter()

        assert curr_metrics.get_task_count() == 0
        assert counter.get() == 0

    def test_get_upstream_counts(self):
        """``get_upstream_counts`` 应返回各上游到当前节点的数量映射。"""
        metrics = TaskMetrics()
        counter_a = ValueWrapper(value=0)
        counter_b = ValueWrapper(value=0)
        metrics.set_upstream_counter("src_a", counter_a)
        metrics.set_upstream_counter("src_b", counter_b)

        counter_a.add(3)
        counter_b.add(5)

        assert metrics.get_upstream_counts() == {"src_a": 3, "src_b": 5}

    def test_get_downstream_counts(self):
        """``get_downstream_counts`` 应返回当前节点到各下游的数量映射。"""
        metrics = TaskMetrics()
        counter_a = ValueWrapper(value=0)
        counter_b = ValueWrapper(value=0)
        metrics.set_downstream_counter("sink_a", counter_a)
        metrics.set_downstream_counter("sink_b", counter_b)

        metrics.add_downstream_count("sink_a", 2)
        metrics.add_downstream_count("sink_b", 4)

        assert metrics.get_downstream_counts() == {"sink_a": 2, "sink_b": 4}


class TestTaskMetricsDuplicate:
    def test_duplicate_check_disabled_always_false(self):
        """测试去重功能禁用时的行为：相同 Hash 不应被判定为重复"""
        metrics = TaskMetrics(enable_duplicate_check=False)
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_2") is False

    def test_duplicate_check_enabled_detects_repeat(self):
        """测试去重功能启用时的行为：相同 Hash 的后续请求应被判定为重复"""
        metrics = TaskMetrics(enable_duplicate_check=True)
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_1") is True
        assert metrics.is_duplicate(b"hash_2") is False

    def test_duplicate_check_resets_with_reset_state(self):
        """测试状态重置对去重集合的影响：reset_state 后历史 Hash 应失效"""
        metrics = TaskMetrics(enable_duplicate_check=True)
        metrics.is_duplicate(b"hash_1")
        assert metrics.is_duplicate(b"hash_1") is True

        metrics.reset_state()
        assert metrics.is_duplicate(b"hash_1") is False


class TestTaskMetricsRetryExceptions:
    def test_default_retry_exceptions_empty(self):
        """测试默认可重试异常配置：默认为空"""
        metrics = TaskMetrics()
        assert metrics.retry_exceptions == ()

    def test_set_retry_exceptions(self):
        """测试动态添加可重试异常类型"""
        metrics = TaskMetrics()
        metrics.set_retry_exceptions(ValueError, RuntimeError)
        assert ValueError in metrics.retry_exceptions
        assert RuntimeError in metrics.retry_exceptions
