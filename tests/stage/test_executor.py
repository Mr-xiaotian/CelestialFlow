from pathlib import Path
from typing import Any

import pytest

from celestialflow import TaskExecutor
from celestialflow.persistence.util_sqlite import append_records
from celestialflow.runtime.util_errors import (
    ConfigurationError,
    ExecutionModeError,
    PersistedError,
)


def build_result_dict(executor: TaskExecutor[Any, Any]) -> dict[Any, Any]:
    """按当前公开接口组装任务到结果/错误字符串的映射。"""
    result_dict = {}
    if executor.persist_result:
        result_dict.update(dict(executor.get_success_pairs()))
    for task, error in executor.get_error_pairs():
        result_dict[task] = str(error)
    return result_dict


# =========================
# 快速测试函数（无副作用）
# =========================
def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


def double(x: int) -> int:
    """测试用同步乘二函数。"""
    return x * 2


def raise_on_negative(x: int) -> int:
    """测试用函数，负数时抛出异常。"""
    if x < 0:
        raise ValueError(f"negative value: {x}")
    return x * 10


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


async def async_double(x: int) -> int:
    """测试用异步乘二函数。"""
    return x * 2


# =========================
# TaskExecutor 基础测试
# =========================
class TestExecutorSerial:
    def test_serial_basic(self):
        """测试串行执行器的基本任务处理"""
        executor = TaskExecutor("AddOneSerial", add_one, execution_mode="serial")
        tasks = [1, 2, 3, 4, 5]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0
        assert counts["tasks_pending"] == 0

    def test_serial_with_errors(self):
        """测试串行执行器对错误任务的处理与记录"""
        executor = TaskExecutor(
            "RaiseOnNegativeSerial",
            raise_on_negative,
            execution_mode="serial",
        )
        tasks: list[int] = [1, -1, 2, -2, 3]
        executor.start(tasks)

        result_dict = build_result_dict(executor)
        assert "negative value: -1" in result_dict[-1]
        assert "negative value: -2" in result_dict[-2]

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_failed"] == 2

        fallback_pairs = dict(executor.get_error_pairs())
        assert isinstance(fallback_pairs[-1], PersistedError)
        assert fallback_pairs[-1].error_type == "ValueError"
        assert "negative value: -1" in fallback_pairs[-1].error_message
        assert fallback_pairs[-2].error_type == "ValueError"

    def test_serial_retry(self):
        """测试串行执行器的重试机制"""
        call_count = 0

        def flaky(x: int) -> int:
            """前两次抛错，第三次返回偏移后的结果。"""
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError("flaky")
            return x + 100

        executor = TaskExecutor(
            "FlakySerialRetry",
            flaky,
            execution_mode="serial",
            max_retries=2,
        )
        executor.set_retry_exceptions(RuntimeError)
        executor.start([1])

        counts = executor.get_counts()
        # 最终成功，失败计数应为 0（重试不计入最终失败）
        assert counts["tasks_succeeded"] == 1
        assert counts["tasks_failed"] == 0
        assert call_count == 3  # 1 次初始 + 2 次重试

    def test_serial_no_retry_for_unmatched_exception(self):
        """测试执行器在遇到非注册重试异常时不进行重试"""
        executor = TaskExecutor(
            "RaiseOnNegativeNoRetry",
            raise_on_negative,
            execution_mode="serial",
            max_retries=2,
        )
        # 只重试 RuntimeError，但函数抛的是 ValueError
        executor.set_retry_exceptions(RuntimeError)
        executor.start([-1])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 1


class TestExecutorThread:
    def test_thread_basic(self):
        """测试线程池执行器的基本并行处理"""
        executor = TaskExecutor(
            "DoubleThread",
            double,
            execution_mode="thread",
            max_workers=4,
        )
        tasks: list[int] = [1, 2, 3, 4, 5]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0


class TestExecutorAsync:
    @pytest.mark.asyncio
    async def test_async_basic(self):
        """测试异步执行器的基本处理"""
        executor = TaskExecutor(
            "AsyncAddOneExecutor",
            async_add_one,
            execution_mode="async",
            max_workers=4,
        )
        tasks: list[int] = [10, 20, 30]
        await executor.start_async(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3

    @pytest.mark.asyncio
    async def test_async_double(self):
        """测试异步执行器的连续处理逻辑"""
        executor = TaskExecutor(
            "AsyncDoubleExecutor",
            async_double,
            execution_mode="async",
            max_workers=4,
        )
        tasks = list(range(20))
        await executor.start_async(tasks)


class TestExecutorDuplicateCheck:
    def test_duplicate_check_disabled_by_default(self):
        """测试默认配置下不会启用重复检查。"""
        executor = TaskExecutor(
            "AddOneDedupDefaultDisabled",
            add_one,
            execution_mode="serial",
        )
        tasks: list[int] = [1, 1, 2, 2, 2, 3]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 6
        assert counts["tasks_duplicated"] == 0

    def test_duplicate_check_enabled(self):
        """测试启用重复检查时，相同任务不重复执行"""
        executor = TaskExecutor(
            "AddOneDedupEnabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,
        )
        tasks: list[int] = [1, 1, 2, 2, 2, 3]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_duplicated"] == 3
        assert counts["tasks_failed"] == 0

    def test_duplicate_check_disabled(self):
        """测试禁用重复检查时，相同任务会被重复执行"""
        executor = TaskExecutor(
            "AddOneDedupDisabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=False,
        )
        tasks: list[int] = [1, 1, 2, 2, 2, 3]
        executor.start(tasks)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 6
        assert counts["tasks_duplicated"] == 0


class TestExecutorReplay:
    def test_start_db(self, tmp_path: Path):
        """执行器应只读取属于自己 stage 的失败任务并启动。"""
        sqlite_path = tmp_path / "fallback.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 2,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "other",
                    "status": "failed",
                    "task_json": 99,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 3.0,
                },
            ],
        )
        assert appended == 3

        executor = TaskExecutor("s1", add_one, execution_mode="serial")
        executor.start_db(sqlite_path)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 2
        assert counts["tasks_failed"] == 0


class TestExecutorSuccessCache:
    def test_success_persist(self):
        """测试结果缓存机制：相同输入直接返回缓存结果"""
        executor = TaskExecutor(
            "AddOneSuccessCache",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,
            persist_result=True,
        )
        executor.start([1, 2, 3])

        pairs = executor.get_success_pairs()
        result_dict = dict(pairs)
        assert result_dict[1] == 2
        assert result_dict[2] == 3
        assert result_dict[3] == 4


class TestExecutorConfig:
    def test_rejects_zero_argument_func(self):
        """测试执行函数没有参数时应直接报配置错误。"""

        def no_args() -> int:
            return 1

        with pytest.raises(ConfigurationError):
            TaskExecutor("NoArgsExecutor", no_args, execution_mode="serial")

    def test_rejects_multi_argument_func(self):
        """测试执行函数存在多个参数时应直接报配置错误。"""

        def two_args(x: int, y: int) -> int:
            return x + y

        with pytest.raises(ConfigurationError):
            TaskExecutor("TwoArgsExecutor", two_args, execution_mode="serial")

    def test_invalid_execution_mode(self):
        """测试配置非法执行模式时抛出异常"""
        with pytest.raises(ExecutionModeError):
            TaskExecutor("AddOneInvalidMode", add_one, execution_mode="invalid")

    def test_get_summary(self):
        """测试获取执行器状态摘要信息"""
        executor = TaskExecutor("AddOneSummary", add_one, execution_mode="serial")
        summary = executor.get_summary()
        assert summary["name"] == "AddOneSummary"
        assert summary["func_name"] == "add_one"
        assert summary["execution_mode"] == "serial"
