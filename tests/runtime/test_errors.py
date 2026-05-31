from celestialflow.runtime.util_errors import (
    CelestialFlowError,
    CelestialFlowTimeoutError,
    CelestialTreeConnectionError,
    ConfigurationError,
    DuplicateNodeError,
    ExecutionModeError,
    GraphStructureError,
    InitializationError,
    InvalidOptionError,
    LogLevelError,
    RemoteWorkerError,
    ReporterError,
    RuntimeStateError,
    ScheduleModeError,
    StageModeError,
    TaskFormatError,
    TerminationMergeError,
    UnconsumedError,
    UnknownNodeError,
)


class TestUtilErrors:
    """验证 util_errors.py 中所有自定义异常类可以正常实例化、继承正确、消息有意义。"""

    # ---- 基础异常 ----

    def test_celestial_flow_error(self):
        """验证 `CelestialFlowError` 可正常保留错误消息。"""
        ex = CelestialFlowError("something went wrong")
        assert isinstance(ex, Exception)
        assert str(ex) == "something went wrong"

    # ---- 配置与选项 ----

    def test_configuration_error(self):
        """验证 `ConfigurationError` 的继承关系与消息。"""
        ex = ConfigurationError("bad config")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "bad config"

    def test_invalid_option_error(self):
        """验证 `InvalidOptionError` 会记录字段和值信息。"""
        ex = InvalidOptionError("timeout", -1, [1, 5, 10])
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, ConfigurationError)
        assert ex.field == "timeout"
        assert ex.value == -1
        assert ex.allowed == (1, 5, 10)
        assert "-1" in str(ex)
        assert "(1, 5, 10)" in str(ex)

    def test_invalid_option_error_custom_prefix(self):
        """验证 `InvalidOptionError` 支持自定义消息前缀。"""
        ex = InvalidOptionError("retries", 0, [1, 2, 3], prefix="Bad")
        assert "Bad " in str(ex)

    def test_execution_mode_error(self):
        """验证 `ExecutionModeError` 会暴露非法执行模式信息。"""
        ex = ExecutionModeError("parallel")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, InvalidOptionError)
        assert ex.execution_mode == "parallel"
        assert ex.valid_modes == ("serial", "thread", "async")
        assert "parallel" in str(ex)

    def test_execution_mode_error_custom_valid_modes(self):
        """验证 `ExecutionModeError` 支持自定义可选模式。"""
        ex = ExecutionModeError("batch", valid_modes=("serial", "batch"))
        assert ex.valid_modes == ("serial", "batch")

    def test_stage_mode_error(self):
        """验证 `StageModeError` 会暴露非法节点模式信息。"""
        ex = StageModeError("process")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, InvalidOptionError)
        assert ex.stage_mode == "process"
        assert ex.valid_modes == ("serial", "thread")
        assert "process" in str(ex)

    def test_log_level_error(self):
        """验证 `LogLevelError` 会暴露非法日志级别信息。"""
        ex = LogLevelError("VERBOSE")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, InvalidOptionError)
        assert ex.log_level == "VERBOSE"
        assert ex.valid_levels == (
            "TRACE",
            "DEBUG",
            "SUCCESS",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        )
        assert "VERBOSE" in str(ex)

    def test_schedule_mode_error(self):
        """验证 `ScheduleModeError` 会暴露非法调度模式信息。"""
        ex = ScheduleModeError("lazy")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, InvalidOptionError)
        assert ex.schedule_mode == "lazy"
        assert ex.valid_modes == ("eager", "staged")
        assert "lazy" in str(ex)

    # ---- 图结构 ----

    def test_graph_structure_error(self):
        """验证 `GraphStructureError` 的继承关系与消息。"""
        ex = GraphStructureError("cycle detected")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, ConfigurationError)
        assert str(ex) == "cycle detected"

    def test_duplicate_node_error(self):
        """验证 `DuplicateNodeError` 的继承关系与消息。"""
        ex = DuplicateNodeError("node A already exists")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, GraphStructureError)
        assert str(ex) == "node A already exists"

    def test_unknown_node_error(self):
        """验证 `UnknownNodeError` 的继承关系与消息。"""
        ex = UnknownNodeError("node X not found")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, GraphStructureError)
        assert str(ex) == "node X not found"

    # ---- 运行时与生命周期 ----

    def test_runtime_state_error(self):
        """验证 `RuntimeStateError` 可正常保留错误消息。"""
        ex = RuntimeStateError("already started")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "already started"

    def test_initialization_error(self):
        """验证 `InitializationError` 继承自 `RuntimeStateError`。"""
        ex = InitializationError("missing dependency")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, RuntimeStateError)
        assert str(ex) == "missing dependency"

    def test_celestial_flow_timeout_error(self):
        """验证 `CelestialFlowTimeoutError` 同时继承超时异常。"""
        ex = CelestialFlowTimeoutError("task timed out")
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, TimeoutError)
        assert str(ex) == "task timed out"

    def test_unconsumed_error(self):
        """验证 `UnconsumedError` 可正常保留错误消息。"""
        ex = UnconsumedError("node output was never consumed")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "node output was never consumed"

    # ---- 外部服务与通信 ----

    def test_remote_worker_error(self):
        """验证 `RemoteWorkerError` 可正常保留错误消息。"""
        ex = RemoteWorkerError("Go Worker returned status 1")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "Go Worker returned status 1"

    def test_reporter_error(self):
        """验证 `ReporterError` 可正常保留错误消息。"""
        ex = ReporterError("reporter connection lost")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "reporter connection lost"

    def test_celestial_tree_connection_error_default_message(self):
        """验证 `CelestialTreeConnectionError` 默认消息可用。"""
        ex = CelestialTreeConnectionError()
        assert isinstance(ex, CelestialFlowError)
        assert "CelestialTreeClient" in str(ex)

    def test_celestial_tree_connection_error_custom_message(self):
        """验证 `CelestialTreeConnectionError` 支持自定义消息。"""
        ex = CelestialTreeConnectionError("custom connection failure")
        assert str(ex) == "custom connection failure"

    # ---- 任务与逻辑 ----

    def test_task_format_error(self):
        """验证 `TaskFormatError` 可正常保留错误消息。"""
        ex = TaskFormatError("malformed task input")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "malformed task input"

    def test_termination_merge_error(self):
        """验证 `TerminationMergeError` 可正常保留错误消息。"""
        ex = TerminationMergeError("merge conflict on termination signal")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "merge conflict on termination signal"


# 运行方式:
#   cd D:\Project\CelestialFlow
#   python -m pytest tests/utils/test_utils_errors.py -v
