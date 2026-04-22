import pytest

from celestialflow.runtime.core_metrics import TaskMetrics


class TestTaskMetricsBasic:
    def test_initial_counts(self):
        """初始计数器应为 0"""
        metrics = TaskMetrics(execution_mode="serial")
        counts = metrics.get_counts()
        assert counts["tasks_input"] == 0
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 0
        assert counts["tasks_duplicated"] == 0
        assert counts["tasks_processed"] == 0
        assert counts["tasks_pending"] == 0

    def test_add_task_count(self):
        """添加任务总数"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(5)
        assert metrics.get_task_count() == 5
        assert metrics.get_counts()["tasks_input"] == 5

    def test_add_success_count(self):
        """添加成功计数"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_success_count(3)
        assert metrics.get_success_count() == 3
        assert metrics.get_counts()["tasks_succeeded"] == 3

    def test_add_error_count(self):
        """添加失败计数"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_error_count(2)
        assert metrics.get_error_count() == 2
        assert metrics.get_counts()["tasks_failed"] == 2

    def test_add_duplicate_count(self):
        """添加重复计数"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_duplicate_count(4)
        assert metrics.get_duplicate_count() == 4
        assert metrics.get_counts()["tasks_duplicated"] == 4

    def test_processed_equals_sum(self):
        """已处理 = 成功 + 失败 + 重复"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.add_error_count(2)
        metrics.add_duplicate_count(1)

        counts = metrics.get_counts()
        assert counts["tasks_processed"] == 8
        assert counts["tasks_pending"] == 2

    def test_is_tasks_finished_true(self):
        """所有任务完成后返回 True"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(3)
        metrics.add_success_count(2)
        metrics.add_error_count(1)
        assert metrics.is_tasks_finished() is True

    def test_is_tasks_finished_false(self):
        """仍有未处理任务时返回 False"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(5)
        metrics.add_success_count(2)
        assert metrics.is_tasks_finished() is False

    def test_reset_counter(self):
        """重置计数器后归零"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_task_count(10)
        metrics.add_success_count(5)
        metrics.reset_counter()
        assert metrics.get_task_count() == 0
        assert metrics.get_success_count() == 0


class TestTaskMetricsDuplicate:
    def test_duplicate_check_disabled_always_false(self):
        """禁用去重时，is_duplicate 永远返回 False"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=False)
        assert metrics.is_duplicate("hash_1") is False
        assert metrics.is_duplicate("hash_1") is False
        assert metrics.is_duplicate("hash_2") is False

    def test_duplicate_check_enabled_detects_repeat(self):
        """启用去重时，第二次相同 hash 返回 True"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)
        assert metrics.is_duplicate("hash_1") is False
        assert metrics.is_duplicate("hash_1") is True
        assert metrics.is_duplicate("hash_2") is False

    def test_duplicate_check_resets_with_reset_state(self):
        """reset_state 后去重集合被清空"""
        metrics = TaskMetrics(execution_mode="serial", enable_duplicate_check=True)
        metrics.is_duplicate("hash_1")
        assert metrics.is_duplicate("hash_1") is True

        metrics.reset_state()
        assert metrics.is_duplicate("hash_1") is False


class TestTaskMetricsRetryExceptions:
    def test_default_retry_exceptions_empty(self):
        """默认无可重试异常"""
        metrics = TaskMetrics(execution_mode="serial")
        assert metrics.retry_exceptions == ()

    def test_add_retry_exceptions(self):
        """添加可重试异常"""
        metrics = TaskMetrics(execution_mode="serial")
        metrics.add_retry_exceptions(ValueError, RuntimeError)
        assert ValueError in metrics.retry_exceptions
        assert RuntimeError in metrics.retry_exceptions
