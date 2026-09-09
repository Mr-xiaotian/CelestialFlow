"""Tests for :mod:`celestialflow.node.core_node`."""

import pytest

from celestialflow import TaskExecutor
from celestialflow.runtime.util_errors import InvalidOptionError


def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


class TestBaseTaskNodeConfig:
    """覆盖 ``BaseTaskNode`` 提供的通用配置与绑定行为。"""

    def test_node_name_identity(self) -> None:
        """节点唯一标识应直接来自 ``name``。"""
        node = TaskExecutor("MyNode", add_one)
        assert node.get_name() == "MyNode"

    def test_node_name_changes_with_name(self) -> None:
        """修改名称后，节点唯一标识应同步更新。"""
        node = TaskExecutor("OldName", add_one)

        old_name = node.get_name()
        node.set_name("NewName")

        assert old_name != node.get_name()
        assert node.get_name() == "NewName"

    def test_valid_execution_mode_serial(self) -> None:
        """支持 ``serial`` 执行模式。"""
        node = TaskExecutor("AddOneSerialExec", add_one, execution_mode="serial")
        assert node.execution_mode == "serial"

    def test_valid_execution_mode_thread(self) -> None:
        """支持 ``thread`` 执行模式。"""
        node = TaskExecutor("AddOneThreadExec", add_one, execution_mode="thread")
        assert node.execution_mode == "thread"

    def test_valid_execution_mode_async(self) -> None:
        """支持 ``async`` 执行模式。"""
        node = TaskExecutor("AddOneAsyncExec", async_add_one, execution_mode="async")
        assert node.execution_mode == "async"

    def test_invalid_execution_mode(self) -> None:
        """非法执行模式应抛出 ``InvalidOptionError``。"""
        with pytest.raises(InvalidOptionError):
            TaskExecutor("AddOneInvalidExecMode", add_one, execution_mode="invalid")

    def test_snapshot_contains_execution_mode(self) -> None:
        """快照应暴露当前执行模式。"""
        node = TaskExecutor(
            "AddOneThreadExec",
            add_one,
            execution_mode="thread",
        )

        snapshot = node.snapshot(interval=0.1)

        assert snapshot["execution_mode"] == "thread"

    def test_prev_binding_survives_execution_mode_switch(self) -> None:
        """切换执行模式不应破坏已建立的前驱绑定。"""
        prev_node = TaskExecutor("PrevNode", add_one)
        current_node = TaskExecutor("CurrentNode", add_one)

        current_node.prev_binding(prev_node)
        prev_node.metrics.add_success_count(2)
        assert current_node.metrics.get_task_count() == 2

        current_node.set_execution_mode("thread")
        assert current_node.metrics.get_task_count() == 2

        prev_node.metrics.add_success_count(1)
        assert current_node.metrics.get_task_count() == 3


class TestBaseTaskNodeStartErrors:
    """覆盖 ``BaseTaskNode.start*`` 的异常聚合行为。"""

    def test_start_raises_exception_group_after_finish(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """同步 ``start`` 应在 finish 后统一抛出收集到的异常。"""
        node = TaskExecutor("NodeErrorGroupSync", add_one, execution_mode="serial")

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(node, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            node,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            node.start()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]

    @pytest.mark.asyncio
    async def test_start_async_raises_exception_group_after_finish(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """异步 ``start_async`` 应在 finish 后统一抛出收集到的异常。"""
        node = TaskExecutor("NodeErrorGroupAsync", async_add_one, execution_mode="async")

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(node, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            node,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            await node.start_async()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]
