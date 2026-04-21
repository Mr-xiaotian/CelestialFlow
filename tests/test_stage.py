import pytest

from celestialflow import TaskStage
from celestialflow.runtime.util_errors import ExecutionModeError, PickleError, StageModeError


# =========================
# 快速测试函数
# =========================
def add_one(x):
    return x + 1


# =========================
# TaskStage 配置测试
# =========================
class TestTaskStageConfig:
    def test_stage_tag_auto_generation(self):
        """tag 自动生成：包含 name 和 func_name"""
        stage = TaskStage(add_one, stage_name="MyStage")
        tag = stage.get_tag()
        assert "MyStage" in tag
        assert "add_one" in tag

    def test_stage_tag_changes_with_name(self):
        """修改 name 后 tag 应失效并重新生成"""
        stage = TaskStage(add_one, stage_name="OldName")
        old_tag = stage.get_tag()
        stage.set_stage_name("NewName")
        new_tag = stage.get_tag()
        assert old_tag != new_tag
        assert "NewName" in new_tag

    def test_valid_stage_mode_serial(self):
        """合法 stage_mode: serial"""
        stage = TaskStage(add_one, stage_mode="serial")
        assert stage.get_stage_mode() == "serial"

    def test_valid_stage_mode_process(self):
        """合法 stage_mode: process"""
        stage = TaskStage(add_one, stage_mode="process")
        assert stage.get_stage_mode() == "process"

    def test_invalid_stage_mode(self):
        """非法 stage_mode 应抛出 StageModeError"""
        with pytest.raises(StageModeError):
            TaskStage(add_one, stage_mode="invalid")

    def test_valid_execution_mode_serial(self):
        """合法 execution_mode: serial"""
        stage = TaskStage(add_one, execution_mode="serial")
        assert stage.execution_mode == "serial"

    def test_valid_execution_mode_thread(self):
        """合法 execution_mode: thread"""
        stage = TaskStage(add_one, execution_mode="thread")
        assert stage.execution_mode == "thread"

    def test_invalid_execution_mode(self):
        """非法 execution_mode 应抛出 ExecutionModeError"""
        with pytest.raises(ExecutionModeError):
            TaskStage(add_one, execution_mode="invalid")

    def test_summary_contains_stage_mode(self):
        """summary 包含 stage_mode 字段"""
        stage = TaskStage(add_one, stage_mode="process", execution_mode="thread")
        summary = stage.get_summary()
        assert summary["stage_mode"] == "process"
        assert summary["execution_mode"] == "thread-20"


class TestTaskStagePickleGuard:
    def test_unpickleable_lambda_raises(self):
        """lambda 无法 pickle，应抛出 PickleError"""
        with pytest.raises(PickleError):
            TaskStage(lambda x: x + 1, stage_mode="process")

    def test_picklable_function_ok(self):
        """普通函数可以正常创建"""
        stage = TaskStage(add_one, stage_mode="process")
        assert stage.func is add_one
