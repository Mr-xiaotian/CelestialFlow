from celestialflow.runtime.core_metrics import TaskMetrics


class TestTaskMetricsBasic:
    def test_initial_counts(self):
        """测试 TaskMetrics 的初始计数器状态：所有指标应默认为 0"""
        metrics = TaskMetrics(execution_mode="serial")
        counts = metrics.get_counts()
        assert counts["tasks_input"] == 0
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 0
        assert counts["tasks_duplicated"] == 0
        assert counts["tasks_processed"] == 0
        assert counts["tasks_pending"] == 0

    def test_add_task_count(self):
        """测试任务总数的累加逻辑"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(5)
        assert metrics.get_task_count() == 5
        assert metrics.get_counts()["tasks_input"] == 5

    def test_add_success_count(self):
        """测试任务成功计数的累加逻辑"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_success_count(3)
        assert metrics.get_success_count() == 3
        assert metrics.get_counts()["tasks_succeeded"] == 3

    def test_add_error_count(self):
        """测试任务失败计数的累加逻辑"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_error_count(2)
        assert metrics.get_error_count() == 2
        assert metrics.get_counts()["tasks_failed"] == 2

    def test_add_duplicate_count(self):
        """测试重复任务计数的累加逻辑"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_duplicate_count(4)
        assert metrics.get_duplicate_count() == 4
        assert metrics.get_counts()["tasks_duplicated"] == 4

    def test_processed_equals_sum(self):
        """测试已处理任务数的计算公式：Processed = Success + Failed + Duplicate"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.add_error_count(2)
        metrics.add_duplicate_count(1)

        counts = metrics.get_counts()
        assert counts["tasks_processed"] == 8
        assert counts["tasks_pending"] == 2

    def test_is_tasks_finished_true(self):
        """测试任务完成状态判定：当已处理数等于总数时应返回 True"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(3)
        metrics.add_success_count(2)
        metrics.add_error_count(1)
        assert metrics.is_tasks_finished() is True

    def test_is_tasks_finished_false(self):
        """测试任务完成状态判定：仍有未处理任务（Pending > 0）时应返回 False"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(5)
        metrics.add_success_count(2)
        assert metrics.is_tasks_finished() is False

    def test_reset_counter(self):
        """测试计数器重置功能：所有累加指标应归零"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.reset_counter()
        assert metrics.get_task_count() == 0
        assert metrics.get_success_count() == 0

    def test_set_execution_mode_keeps_counters_and_lock_stable(self):
        """测试切换 execution_mode 时不重建锁和计数器对象"""
        metrics = TaskMetrics(execution_mode="serial")
        lock = metrics.lock
        task_counter = metrics.task_counter
        success_counter = metrics.success_counter

        metrics.add_task_count(3)
        metrics.add_success_count(2)
        metrics.set_execution_mode("thread")

        assert metrics.execution_mode == "thread"
        assert metrics.lock is lock
        assert metrics.task_counter is task_counter
        assert metrics.success_counter is success_counter
        assert metrics.get_task_count() == 3
        assert metrics.get_success_count() == 2


class TestTaskMetricsDuplicate:
    def test_duplicate_check_disabled_always_false(self):
        """测试去重功能禁用时的行为：相同 Hash 不应被判定为重复"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=False)
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_2") is False

    def test_duplicate_check_enabled_detects_repeat(self):
        """测试去重功能启用时的行为：相同 Hash 的后续请求应被判定为重复"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)
        assert metrics.is_duplicate(b"hash_1") is False
        assert metrics.is_duplicate(b"hash_1") is True
        assert metrics.is_duplicate(b"hash_2") is False

    def test_duplicate_check_resets_with_reset_state(self):
        """测试状态重置对去重集合的影响：reset_state 后历史 Hash 应失效"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)
        metrics.is_duplicate(b"hash_1")
        assert metrics.is_duplicate(b"hash_1") is True

        metrics.reset_state()
        assert metrics.is_duplicate(b"hash_1") is False


class TestTaskMetricsRetryExceptions:
    def test_default_retry_exceptions_empty(self):
        """测试默认可重试异常配置：默认为空"""
        metrics = TaskMetrics(execution_mode="serial")
        assert metrics.retry_exceptions == ()

    def test_add_retry_exceptions(self):
        """测试动态添加可重试异常类型"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_retry_exceptions(ValueError, RuntimeError)
        assert ValueError in metrics.retry_exceptions
        assert RuntimeError in metrics.retry_exceptions
