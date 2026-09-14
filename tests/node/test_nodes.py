"""Tests for :mod:`celestialflow.node.core_nodes`."""

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest

from celestialflow import TaskExecutor, TaskGraph, TaskRouter, TaskSplitter
from celestialflow.persistence.util_sqlite import append_records
from celestialflow.runtime.util_errors import (
    ConfigurationError,
    PersistedError,
)


def build_result_dict(executor: TaskExecutor[Any, Any]) -> dict[Any, Any]:
    """按当前公开接口组装任务到结果或错误字符串的映射。"""
    result_dict = dict(executor.get_success_pairs())
    for task, error in executor.get_error_pairs():
        result_dict[task] = str(error)
    return result_dict


def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


def double(x: int) -> int:
    """测试用同步乘二函数。"""
    return x * 2


def raise_on_negative(x: int) -> int:
    """负数时抛出异常的测试函数。"""
    if x < 0:
        raise ValueError(f"negative value: {x}")
    return x * 10


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


async def async_double(x: int) -> int:
    """测试用异步乘二函数。"""
    return x * 2


def split_identity(task: Iterable[int]) -> Iterable[int]:
    """测试用恒等拆分函数：原样返回输入的可迭代对象。"""
    return task


class TestTaskExecutor:
    """覆盖 ``TaskExecutor`` 的执行、回放和配置行为。"""

    def test_serial_basic(self) -> None:
        """串行执行器应能顺序处理全部任务。"""
        executor = TaskExecutor("AddOneSerial", add_one, execution_mode="serial")
        executor.run([1, 2, 3, 4, 5])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0
        assert counts["tasks_pending"] == 0

    def test_serial_with_errors(self) -> None:
        """串行执行器应能记录失败任务及其持久化错误。"""
        executor = TaskExecutor(
            "RaiseOnNegativeSerial",
            raise_on_negative,
            execution_mode="serial",
        )
        executor.run([1, -1, 2, -2, 3])

        result_dict = build_result_dict(executor)
        assert "negative value: -1" in result_dict[-1]
        assert "negative value: -2" in result_dict[-2]

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_failed"] == 2

        lifecycle_pairs = dict(executor.get_error_pairs())
        assert isinstance(lifecycle_pairs[-1], PersistedError)
        assert lifecycle_pairs[-1].error_type == "ValueError"
        assert "negative value: -1" in lifecycle_pairs[-1].error_message
        assert lifecycle_pairs[-2].error_type == "ValueError"

    def test_serial_retry(self) -> None:
        """命中可重试异常时应在耗尽前继续重试。"""
        call_count = 0

        def flaky(x: int) -> int:
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
        executor.run([1])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 1
        assert counts["tasks_failed"] == 0
        assert call_count == 3

    def test_serial_no_retry_for_unmatched_exception(self) -> None:
        """未注册为可重试的异常不应触发重试。"""
        executor = TaskExecutor(
            "RaiseOnNegativeNoRetry",
            raise_on_negative,
            execution_mode="serial",
            max_retries=2,
        )
        executor.set_retry_exceptions(RuntimeError)
        executor.run([-1])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 0
        assert counts["tasks_failed"] == 1

    def test_thread_basic(self) -> None:
        """线程模式应能并行处理一批任务。"""
        executor = TaskExecutor(
            "DoubleThread",
            double,
            execution_mode="thread",
            max_workers=4,
        )
        executor.run([1, 2, 3, 4, 5])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 5
        assert counts["tasks_failed"] == 0

    @pytest.mark.asyncio
    async def test_async_basic(self) -> None:
        """异步模式应能处理一批任务。"""
        executor = TaskExecutor(
            "AsyncAddOneExecutor",
            async_add_one,
            execution_mode="async",
            max_workers=4,
        )
        await executor.run_async([10, 20, 30])

        assert executor.get_counts()["tasks_succeeded"] == 3

    @pytest.mark.asyncio
    async def test_async_double(self) -> None:
        """异步执行器应能连续处理多个任务。"""
        executor = TaskExecutor(
            "AsyncDoubleExecutor",
            async_double,
            execution_mode="async",
            max_workers=4,
        )
        await executor.run_async(list(range(20)))

        assert executor.get_counts()["tasks_succeeded"] == 20

    def test_duplicate_check_disabled_by_default(self) -> None:
        """默认配置下不应启用重复检查。"""
        executor = TaskExecutor(
            "AddOneDedupDefaultDisabled",
            add_one,
            execution_mode="serial",
        )
        executor.run([1, 1, 2, 2, 2, 3])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 6
        assert counts["tasks_duplicated"] == 0

    def test_duplicate_check_enabled(self) -> None:
        """启用重复检查时，相同任务不应重复执行。"""
        executor = TaskExecutor(
            "AddOneDedupEnabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,
        )
        executor.run([1, 1, 2, 2, 2, 3])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_duplicated"] == 3
        assert counts["tasks_failed"] == 0

    def test_duplicate_check_disabled(self) -> None:
        """显式关闭重复检查时，相同任务应重复执行。"""
        executor = TaskExecutor(
            "AddOneDedupDisabled",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=False,
        )
        executor.run([1, 1, 2, 2, 2, 3])

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 6
        assert counts["tasks_duplicated"] == 0

    def test_restore_db(self, tmp_path: Path) -> None:
        """默认应读取属于自己名称的 failed 与 pending 任务。"""
        sqlite_path = tmp_path / "lifecycle.sqlite3"
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
                    "stage": "s1",
                    "status": "pending",
                    "task_json": 3,
                    "error_type": "",
                    "error_message": "",
                    "ts": 3.0,
                },
                {
                    "event_id": 4,
                    "stage": "other",
                    "status": "failed",
                    "task_json": 99,
                    "error_type": "ValueError",
                    "error_message": "bad",
                    "ts": 4.0,
                },
            ],
        )
        assert appended == 4

        executor = TaskExecutor("s1", add_one, execution_mode="serial")
        executor.restore_db(sqlite_path)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 3
        assert counts["tasks_failed"] == 0

    def test_restore_db_filters_error_type_when_enabled(
        self, tmp_path: Path
    ) -> None:
        """开启错误类型过滤时只回放命中 retry_exceptions 的记录。"""
        sqlite_path = tmp_path / "lifecycle.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad value",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 2,
                    "error_type": "RuntimeError",
                    "error_message": "boom",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 3,
                    "error_type": "RuntimeError",
                    "error_message": "boom again",
                    "ts": 3.0,
                },
            ],
        )
        assert appended == 3

        executor = TaskExecutor("s1", add_one, execution_mode="serial")
        executor.set_retry_exceptions(RuntimeError)
        executor.restore_db(
            sqlite_path,
            statuses=["failed"],
            filter_by_error_type=True,
        )

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 2
        assert counts["tasks_failed"] == 0

    def test_restore_db_filter_keeps_pending_records(self, tmp_path: Path) -> None:
        """开启错误类型过滤时仍应保留 pending 记录。"""
        sqlite_path = tmp_path / "lifecycle.sqlite3"
        appended = append_records(
            sqlite_path,
            [
                {
                    "event_id": 1,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 1,
                    "error_type": "ValueError",
                    "error_message": "bad value",
                    "ts": 1.0,
                },
                {
                    "event_id": 2,
                    "stage": "s1",
                    "status": "failed",
                    "task_json": 2,
                    "error_type": "RuntimeError",
                    "error_message": "boom",
                    "ts": 2.0,
                },
                {
                    "event_id": 3,
                    "stage": "s1",
                    "status": "pending",
                    "task_json": 3,
                    "error_type": "",
                    "error_message": "",
                    "ts": 3.0,
                },
            ],
        )
        assert appended == 3

        executor = TaskExecutor("s1", add_one, execution_mode="serial")
        executor.set_retry_exceptions(RuntimeError)
        executor.restore_db(sqlite_path, filter_by_error_type=True)

        counts = executor.get_counts()
        assert counts["tasks_succeeded"] == 2
        assert counts["tasks_failed"] == 0

    def test_success_persist(self) -> None:
        """成功结果应能通过生命周期缓存读回。"""
        executor = TaskExecutor(
            "AddOneSuccessCache",
            add_one,
            execution_mode="serial",
            enable_duplicate_check=True,
        )
        executor.run([1, 2, 3])

        result_dict = dict(executor.get_success_pairs())
        assert result_dict[1] == 2
        assert result_dict[2] == 3
        assert result_dict[3] == 4

    def test_rejects_zero_argument_func(self) -> None:
        """执行函数没有参数时应直接报配置错误。"""

        def no_args() -> int:
            return 1

        with pytest.raises(ConfigurationError):
            TaskExecutor("NoArgsExecutor", no_args, execution_mode="serial")

    def test_rejects_multi_argument_func(self) -> None:
        """执行函数存在多个参数时应直接报配置错误。"""

        def two_args(x: int, y: int) -> int:
            return x + y

        with pytest.raises(ConfigurationError):
            TaskExecutor("TwoArgsExecutor", two_args, execution_mode="serial")

    def test_name_and_execution_mode(self) -> None:
        """任务执行器应暴露自身名称和执行模式。"""
        executor = TaskExecutor("AddOneSummary", add_one, execution_mode="serial")
        assert executor.get_name() == "AddOneSummary"
        assert executor.execution_mode == "serial"


class TestTaskSplitter:
    """覆盖 ``TaskSplitter`` 的拆分行为。"""

    def test_splitter_init(self) -> None:
        """TaskSplitter 默认应为串行执行模式，且尚未绑定下游。"""
        splitter = TaskSplitter("Splitter", split_identity)
        assert splitter.execution_mode == "serial"
        assert splitter.metrics.downstream_counter == {}

    def test_splitter_process_success(self) -> None:
        """拆分成功后，下游应收到独立子任务。"""

        def noop(x: int) -> int:
            return x

        splitter = TaskSplitter("S", split_identity)
        worker = TaskExecutor("A", noop)

        graph = TaskGraph("test_splitter_process_success")
        graph.set_nodes([splitter, worker])
        graph.connect([splitter], [worker])
        graph.run({"S": [[1, 2, 3]]})

        # 每个子任务应作为独立任务到达下游
        assert splitter.metrics.downstream_counter["A"].get() == 1
        assert worker.get_counts()["tasks_succeeded"] == 3

    def test_splitter_allows_empty_iterable(self) -> None:
        """空可迭代对象应产生 0 个子任务，而不是抛异常。"""

        def noop(x: int) -> int:
            return x

        splitter = TaskSplitter("S", split_identity)
        worker = TaskExecutor("A", noop)

        graph = TaskGraph("test_splitter_allows_empty_iterable")
        graph.set_nodes([splitter, worker])
        graph.connect([splitter], [worker])
        graph.run({"S": [[]]})

        assert splitter.metrics.downstream_counter["A"].get() == 1
        assert worker.get_counts()["tasks_succeeded"] == 0

    def test_splitter_supports_generator_input(self) -> None:
        """一次性迭代器也应能被完整拆分并继续分发。"""

        def noop(x: int) -> int:
            return x

        splitter = TaskSplitter("S", split_identity)
        worker = TaskExecutor("A", noop)

        graph = TaskGraph("test_splitter_supports_generator_input")
        graph.set_nodes([splitter, worker])
        graph.connect([splitter], [worker])
        graph.run({"S": [(i for i in [1, 2, 3])]})

        assert splitter.metrics.downstream_counter["A"].get() == 1
        assert worker.get_counts()["tasks_succeeded"] == 3

    def test_splitter_custom_func_transforms_items(self) -> None:
        """自定义拆分函数应能对子任务做变换后再分发。"""

        def noop(x: str) -> str:
            return x

        splitter = TaskSplitter(
            "S",
            lambda task: (item.strip() for item in task),
        )
        worker = TaskExecutor("A", noop)

        graph = TaskGraph("test_splitter_custom_func_transforms_items")
        graph.set_nodes([splitter, worker])
        graph.connect([splitter], [worker])
        graph.run({"S": [[" a ", " b ", " c "]]})

        assert splitter.metrics.downstream_counter["A"].get() == 1
        assert sorted(task for task, _ in worker.get_success_pairs()) == ["a", "b", "c"]


class TestTaskRouter:
    """覆盖 ``TaskRouter`` 的路由行为。"""

    def test_router_init(self) -> None:
        """TaskRouter 默认应为串行执行模式，且尚未绑定下游。"""
        router = TaskRouter("Router", lambda task: (str(task), task))
        assert router.execution_mode == "serial"
        assert router.metrics.downstream_counter == {}

    def test_router_func_returns_target_and_task(self) -> None:
        """路由函数应返回 ``(target, task)`` 二元组。"""
        router = TaskRouter(
            "Router",
            lambda task: ("target1", task) if task == "data" else ("unknown", task),
        )
        assert router.func("data") == ("target1", "data")

    def test_router_process_success(self) -> None:
        """路由成功后，任务应被发送到指定目标节点。"""

        def noop(x: str) -> str:
            return x

        router = TaskRouter(
            "R",
            lambda task: ("target1", task) if task == "msg1" else ("target2", task),
        )
        target1 = TaskExecutor("target1", noop)
        target2 = TaskExecutor("target2", noop)

        graph = TaskGraph("test_router_process_success")
        graph.set_nodes([router, target1, target2])
        graph.connect([router], [target1, target2])
        graph.run({"R": ["msg1", "msg2"]})

        # 每个目标节点应收到一次向下游的发送计数
        assert router.metrics.downstream_counter["target1"].get() == 1
        assert router.metrics.downstream_counter["target2"].get() == 1
        assert target1.get_counts()["tasks_succeeded"] == 1
        assert target2.get_counts()["tasks_succeeded"] == 1

    def test_router_binding_counter_stable_across_mode_switch(self) -> None:
        """绑定计数器应跨执行模式切换保持稳定。"""
        router = TaskRouter("Router", lambda task: ("target1", task))
        target = TaskExecutor("target1", lambda task: task)

        router.connect_to(target)
        counter = router.metrics.downstream_counter["target1"]
        assert target.metrics.upstream_counter["Router"] is counter

        router.set_execution_mode("thread")

        assert target.metrics.upstream_counter["Router"] is counter
