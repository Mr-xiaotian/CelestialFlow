import pytest

from celestialflow import TaskStage
from celestialflow.runtime.util_errors import (
    ExecutionModeError,
    StageModeError,
)


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

    def test_valid_stage_mode_serial(self):
        """测试合法节点模式：serial（串行隔离）"""
        stage = TaskStage("AddOneSerialMode", add_one, stage_mode="serial")
        assert stage.get_stage_mode() == "serial"

    def test_valid_stage_mode_thread(self):
        """测试合法节点模式：thread（线程隔离）"""
        stage = TaskStage("AddOneThreadMode", add_one, stage_mode="thread")
        assert stage.get_stage_mode() == "thread"

    def test_invalid_stage_mode(self):
        """测试非法节点模式配置：应抛出特定的 StageModeError 异常"""
        with pytest.raises(StageModeError):
            TaskStage("AddOneInvalidStageMode", add_one, stage_mode="invalid")

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
        with pytest.raises(ExecutionModeError):
            TaskStage("AddOneInvalidExecMode", add_one, execution_mode="invalid")

    def test_summary_contains_stage_mode(self):
        """测试 Stage 的状态摘要信息是否包含节点模式及其执行配置"""
        stage = TaskStage(
            "AddOneThreadExec",
            add_one,
            stage_mode="thread",
            execution_mode="thread",
        )
        summary = stage.get_summary()
        assert summary["stage_mode"] == "thread"
        assert summary["execution_mode"] == "thread"

    def test_lambda_allowed_in_thread(self):
        """测试在 thread 隔离模式下允许使用匿名函数（lambda）"""
        stage = TaskStage("LambdaThreadAllowed", lambda x: x + 1, stage_mode="thread")
        assert stage.get_stage_mode() == "thread"

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
