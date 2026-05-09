# runtime/util_errors.py
from __future__ import annotations

from collections.abc import Iterable
from typing import Any


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
        """
        :param field: 配置项名称
        :param value: 实际传入的值
        :param allowed: 允许的取值集合
        :param prefix: 错误消息前缀
        """
        allowed_tuple: tuple[Any, ...] = tuple(allowed)
        message = f"{prefix} {field}: {value}. Valid options are {allowed_tuple}."
        super().__init__(message)

        self.field = field
        self.value = value
        self.allowed = allowed_tuple


class ExecutionModeError(InvalidOptionError):
    """非法的 execution_mode 配置错误"""

    def __init__(self, execution_mode: str, valid_modes=None):
        """
        :param execution_mode: 非法的执行模式值
        :param valid_modes: 允许的执行模式列表
        """
        valid_modes = valid_modes or ("serial", "thread", "async")
        super().__init__("execution mode", execution_mode, valid_modes)
        self.execution_mode = execution_mode
        self.valid_modes = self.allowed  # 兼容旧字段名


class StageModeError(InvalidOptionError):
    """非法的 stage_mode 配置错误"""

    def __init__(self, stage_mode: str, valid_modes=None):
        """
        :param stage_mode: 非法的节点模式值
        :param valid_modes: 允许的节点模式列表
        """
        valid_modes = valid_modes or ("serial", "thread")
        super().__init__("stage mode", stage_mode, valid_modes)
        self.stage_mode = stage_mode
        self.valid_modes = self.allowed


class LogLevelError(InvalidOptionError):
    """非法的 log_level 配置错误"""

    def __init__(self, log_level: str, valid_levels=None):
        """
        :param log_level: 非法的日志级别值
        :param valid_levels: 允许的日志级别列表
        """
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
    """远端 Worker（如 Go Worker）执行失败或返回异常状态时抛出。"""

    pass


class ScheduleModeError(InvalidOptionError):
    """非法的 schedule_mode 配置错误"""

    def __init__(self, schedule_mode: str, valid_modes=None):
        """
        :param schedule_mode: 非法的调度模式值
        :param valid_modes: 允许的调度模式列表
        """
        valid_modes = valid_modes or ("eager", "staged")
        super().__init__("schedule mode", schedule_mode, valid_modes)
        self.schedule_mode = schedule_mode
        self.valid_modes = self.allowed


class CelestialTreeConnectionError(CelestialFlowError):
    """CelestialTree 客户端连接失败"""

    def __init__(self, message: str = "CelestialTreeClient is not available"):
        """
        :param message: 错误消息
        """
        super().__init__(message)


class UnconsumedError(CelestialFlowError):
    """用于标记任务未消费的异常类"""

    pass
