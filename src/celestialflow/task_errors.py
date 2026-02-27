from __future__ import annotations
from typing import Iterable, Tuple, Any


class CelestialFlowError(Exception):
    """CelestialFlow 所有自定义异常的基类"""

    pass


class ConfigurationError(CelestialFlowError):
    """配置错误（参数非法、组合不支持等）"""

    pass


class InvalidOptionError(ConfigurationError):
    """
    某个配置项的取值不合法（不在允许集合里）。
    """

    def __init__(
        self,
        field: str,
        value: Any,
        allowed: Iterable[Any],
        *,
        prefix: str = "Invalid",
    ):
        allowed_tuple: Tuple[Any, ...] = tuple(allowed)
        message = f"{prefix} {field}: {value}. Valid options are {allowed_tuple}."
        super().__init__(message)

        self.field = field
        self.value = value
        self.allowed = allowed_tuple


class ExecutionModeError(InvalidOptionError):
    """非法的 execution_mode 配置错误"""

    def __init__(self, execution_mode: str, valid_modes=None):
        valid_modes = valid_modes or ("serial", "process", "thread", "async")
        super().__init__("execution mode", execution_mode, valid_modes)
        self.execution_mode = execution_mode
        self.valid_modes = self.allowed  # 兼容旧字段名


class StageModeError(InvalidOptionError):
    """非法的 stage_mode 配置错误"""

    def __init__(self, stage_mode: str, valid_modes=None):
        valid_modes = valid_modes or ("serial", "process")
        super().__init__("stage mode", stage_mode, valid_modes)
        self.stage_mode = stage_mode
        self.valid_modes = self.allowed


class LogLevelError(InvalidOptionError):
    """非法的 log_level 配置错误"""

    def __init__(self, log_level: str, valid_levels=None):
        valid_levels = valid_levels or (
            "TRACE",
            "DEBUG",
            "SUCCESS",
            "INFO",
            "WARNING",
            "ERROR",
            "CRITICAL",
        )
        super().__init__("log level", log_level, valid_levels)
        self.log_level = log_level
        self.valid_levels = self.allowed


class RemoteWorkerError(CelestialFlowError):
    pass
