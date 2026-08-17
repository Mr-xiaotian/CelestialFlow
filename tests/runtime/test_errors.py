from celestialflow.runtime.util_errors import (
    CelestialFlowError,
    CelestialFlowTimeoutError,
    ConfigurationError,
    DuplicateNodeError,
    GraphStructureError,
    InitializationError,
    InvalidOptionError,
    RemoteWorkerError,
    ReporterError,
    RuntimeStateError,
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
        """验证非法 execution_mode 会暴露字段信息。"""
        ex = InvalidOptionError("execution mode", "parallel", ("serial", "thread"))
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, ConfigurationError)
        assert ex.field == "execution mode"
        assert ex.value == "parallel"
        assert ex.allowed == ("serial", "thread")
        assert "parallel" in str(ex)

    def test_graph_mode_error(self):
        """验证非法 graph_mode 会暴露字段信息。"""
        ex = InvalidOptionError("graph mode", "process", ("serial", "thread", "async"))
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, ConfigurationError)
        assert ex.field == "graph mode"
        assert ex.value == "process"
        assert ex.allowed == ("serial", "thread", "async")
        assert "process" in str(ex)

    def test_log_level_error(self):
        """验证非法 log_level 会暴露字段信息。"""
        ex = InvalidOptionError(
            "log level", "VERBOSE",
            ("TRACE", "DEBUG", "SUCCESS", "INFO", "WARNING", "ERROR", "CRITICAL"),
        )
        assert isinstance(ex, CelestialFlowError)
        assert isinstance(ex, ConfigurationError)
        assert ex.field == "log level"
        assert ex.value == "VERBOSE"
        assert "VERBOSE" in str(ex)

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

    # ---- 任务与逻辑 ----

    def test_termination_merge_error(self):
        """验证 `TerminationMergeError` 可正常保留错误消息。"""
        ex = TerminationMergeError("merge conflict on termination signal")
        assert isinstance(ex, CelestialFlowError)
        assert str(ex) == "merge conflict on termination signal"


# 运行方式:
#   cd D:\Project\CelestialFlow
#   python -m pytest tests/utils/test_utils_errors.py -v
