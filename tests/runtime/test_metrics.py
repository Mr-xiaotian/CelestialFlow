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
        assert counts["tasks_skipped"] == 0
        assert counts["tasks_processed"] == 0
        assert counts["tasks_pending"] == 0
        assert metrics.get_external_input_count() == 0
        assert metrics.get_upstream_input_count() == 0
        assert metrics.get_upstream_counts() == {}
        assert metrics.get_downstream_counts() == {}

    def test_add_external_input_count(self):
        """测试外部注入任务计数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_external_input_count(5)
        assert metrics.get_external_input_count() == 5
        assert metrics.get_upstream_input_count() == 0
        assert metrics.get_input_count() == 5
        counts = metrics.get_counts()
        assert counts["tasks_input"] == 5

    def test_input_count_split_external_and_upstream(self):
        """外部注入与上游提供的任务应分别计数且合计正确"""
        metrics = TaskMetrics()
        upstream_a = ValueWrapper(value=0)
        upstream_b = ValueWrapper(value=0)
        metrics.set_upstream_counter("src_a", upstream_a)
        metrics.set_upstream_counter("src_b", upstream_b)

        metrics.add_external_input_count(3)
        upstream_a.add(2)
        upstream_b.add(4)

        assert metrics.get_external_input_count() == 3
        assert metrics.get_upstream_input_count() == 6
        assert metrics.get_input_count() == 9

        counts = metrics.get_counts()
        assert counts["tasks_input"] == 9

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

    def test_add_skip_count(self):
        """测试跳过任务计数的累加逻辑"""
        metrics = TaskMetrics()
        metrics.add_skip_count(3)
        assert metrics.get_skip_count() == 3
        assert metrics.get_counts()["tasks_skipped"] == 3

    def test_processed_equals_sum(self):
        """测试已处理任务数的计算公式：Processed = Success + Failed + Skip"""
        metrics = TaskMetrics()
        metrics.add_external_input_count(10)
        metrics.add_success_count(5)
        metrics.add_fail_count(2)
        metrics.add_skip_count(1)

        counts = metrics.get_counts()
        assert counts["tasks_processed"] == 8
        assert counts["tasks_pending"] == 2

    def test_processed_includes_skipped(self):
        """跳过任务应计入已处理数，并影响任务完成判定"""
        metrics = TaskMetrics()
        metrics.add_external_input_count(4)
        metrics.add_success_count(1)
        metrics.add_fail_count(1)
        metrics.add_skip_count(2)

        counts = metrics.get_counts()
        assert counts["tasks_skipped"] == 2
        assert counts["tasks_processed"] == 4
        assert counts["tasks_pending"] == 0
        assert metrics.is_tasks_finished() is True

    def test_is_tasks_finished_true(self):
        """测试任务完成状态判定：当已处理数等于总数时应返回 True"""
        metrics = TaskMetrics()
        metrics.add_external_input_count(3)
        metrics.add_success_count(2)
        metrics.add_fail_count(1)
        assert metrics.is_tasks_finished() is True

    def test_is_tasks_finished_false(self):
        """测试任务完成状态判定：仍有未处理任务（Pending > 0）时应返回 False"""
        metrics = TaskMetrics()
        metrics.add_external_input_count(5)
        metrics.add_success_count(2)
        assert metrics.is_tasks_finished() is False


class TestTaskMetricsBinding:
    """覆盖上游/下游绑定计数器（``connect_to`` 建立的计数关联）。"""

    def test_upstream_counter_adds_to_task_count(self):
        """上游计数器的值应计入任务总数。"""
        metrics = TaskMetrics()
        upstream = ValueWrapper(0)
        metrics.set_upstream_counter("prev", upstream)

        upstream.add(3)

        assert metrics.get_input_count() == 3
        assert metrics.get_upstream_input_count() == 3
        assert metrics.get_external_input_count() == 0

    def test_shared_binding_counter(self):
        """``connect_to`` 双方应共享同一个计数器对象。"""
        prev_metrics = TaskMetrics()
        curr_metrics = TaskMetrics()
        counter = ValueWrapper(value=0)
        prev_metrics.set_downstream_counter("current", counter)
        curr_metrics.set_upstream_counter("prev", counter)

        prev_metrics.add_downstream_count("current", 2)

        assert curr_metrics.get_input_count() == 2

    def test_add_downstream_count_missing_target_raises(self):
        """未注册的下游名称应抛出 ``KeyError``。"""
        metrics = TaskMetrics()
        with pytest.raises(KeyError):
            metrics.add_downstream_count("ghost", 1)

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


class _FakeClock:
    """可手动推进的假时钟，用于替身 ``time.perf_counter``。"""

    def __init__(self, start: float = 1000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        """返回当前假时间。"""
        return self.now

    def advance(self, seconds: float) -> None:
        """把假时间向前推进 ``seconds`` 秒。"""
        self.now += seconds


class TestTaskMetricsElapsed:
    """TaskMetrics — 忙碌墙钟耗时的累计口径。"""

    def test_elapsed_is_zero_without_tasks(self):
        """没有任何任务执行过时耗时为 0（同时保证新增字段已在 __init__ 初始化）。"""
        assert TaskMetrics().get_elapsed() == 0.0

    def test_elapsed_accumulates_only_while_busy(self, monkeypatch: pytest.MonkeyPatch):
        """耗时只在任务实际执行期间累积，空闲区间不计。"""
        clock = _FakeClock()
        monkeypatch.setattr(
            "celestialflow.runtime.core_metrics.time.perf_counter", clock
        )
        metrics = TaskMetrics()

        metrics.begin_task()
        clock.advance(2.0)
        assert metrics.get_elapsed() == 2.0  # 未闭合的时间片也要计入

        metrics.end_task()
        clock.advance(5.0)  # 空闲 5 秒
        assert metrics.get_elapsed() == 2.0

    def test_elapsed_counts_overlapping_tasks_once(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """并发重叠按墙钟计一次：各任务时长之和为 5 秒，这里只应记 3 秒。"""
        clock = _FakeClock()
        monkeypatch.setattr(
            "celestialflow.runtime.core_metrics.time.perf_counter", clock
        )
        metrics = TaskMetrics()

        metrics.begin_task()  # 任务 A 开始（t=1000）
        clock.advance(1.0)
        metrics.begin_task()  # 任务 B 开始时节点已在忙（t=1001）
        clock.advance(2.0)
        assert metrics.get_elapsed() == 3.0

        metrics.end_task()
        metrics.end_task()
        clock.advance(10.0)  # 空闲
        assert metrics.get_elapsed() == 3.0
