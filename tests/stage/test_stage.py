import pytest

from celestialflow import TaskStage
from celestialflow.runtime.util_errors import InvalidOptionError


# =========================
# 快速测试函数
# =========================
def add_one(x: int) -> int:
    """测试用同步加一函数。"""
    return x + 1


async def async_add_one(x: int) -> int:
    """测试用异步加一函数。"""
    return x + 1


# =========================
# TaskStage 配置测试
# =========================
class TestTaskStageConfig:
    def test_stage_name_identity(self):
        """测试 Stage 唯一标识现在直接使用 name"""
        stage = TaskStage("MyStage", add_one)
        assert stage.get_name() == "MyStage"

    def test_stage_name_changes_with_name(self):
        """测试修改节点名称后，唯一标识随之更新"""
        stage = TaskStage("OldName", add_one)
        old_name = stage.get_name()
        stage.set_name("NewName")
        new_name = stage.get_name()
        assert old_name != new_name
        assert new_name == "NewName"

    def test_valid_execution_mode_serial(self):
        """测试合法执行模式：serial（单线程执行）"""
        stage = TaskStage("AddOneSerialExec", add_one, execution_mode="serial")
        assert stage.execution_mode == "serial"

    def test_valid_execution_mode_thread(self):
        """测试合法执行模式：thread（线程池执行）"""
        stage = TaskStage("AddOneThreadExec", add_one, execution_mode="thread")
        assert stage.execution_mode == "thread"

    def test_valid_execution_mode_async(self):
        """测试合法执行模式：async（异步 IO 执行）"""
        stage = TaskStage("add_one_async_exec", async_add_one, execution_mode="async")
        assert stage.execution_mode == "async"

    def test_invalid_execution_mode(self):
        """测试非法执行模式配置：应抛出特定的 ExecutionModeError 异常"""
        with pytest.raises(InvalidOptionError):
            TaskStage("AddOneInvalidExecMode", add_one, execution_mode="invalid")

    def test_summary_contains_execution_mode(self):
        """测试 Stage 的状态摘要信息是否包含执行模式配置"""
        stage = TaskStage(
            "AddOneThreadExec",
            add_one,
            execution_mode="thread",
        )
        summary = stage.get_summary()
        assert summary["execution_mode"] == "thread"

    def test_prev_binding_survives_execution_mode_switch(self):
        """测试前驱绑定在 execution_mode 切换后仍然保留"""
        prev_stage = TaskStage("PrevStage", add_one)
        current_stage = TaskStage("CurrentStage", add_one)

        current_stage.prev_binding(prev_stage)
        prev_stage.metrics.add_success_count(2)
        assert current_stage.metrics.get_task_count() == 2

        current_stage.set_execution_mode("thread")
        assert current_stage.metrics.get_task_count() == 2

        prev_stage.metrics.add_success_count(1)
        assert current_stage.metrics.get_task_count() == 3


class TestTaskStageStartErrors:
    def test_start_raises_exception_group_after_finish(self, monkeypatch):
        """同步 start 应在 finish 后统一抛出收集到的异常。"""
        stage = TaskStage("StageErrorGroupSync", add_one, execution_mode="serial")

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(stage, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            stage,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            stage.start()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]

    @pytest.mark.asyncio
    async def test_start_async_raises_exception_group_after_finish(
        self,
        monkeypatch,
    ):
        """异步 start_async 应在 finish 后统一抛出收集到的异常。"""
        stage = TaskStage("StageErrorGroupAsync", async_add_one, execution_mode="async")

        def crash_prepare() -> None:
            raise ValueError("prepare failed")

        monkeypatch.setattr(stage, "_prepare_start", crash_prepare)
        monkeypatch.setattr(
            stage,
            "_finish_start",
            lambda _start_perf: [RuntimeError("finish failed")],
        )

        with pytest.raises(ExceptionGroup) as exc_info:
            await stage.start_async()

        messages = [str(exception) for exception in exc_info.value.exceptions]
        assert messages == ["prepare failed", "finish failed"]
