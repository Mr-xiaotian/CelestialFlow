# runtime/util_errors.py
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

# ==== 基础异常 ====


class CelestialFlowError(Exception):
    """CelestialFlow 所有自定义异常的基类"""

    pass


# ==== 配置与选项 ====


class ConfigurationError(CelestialFlowError):
    """配置错误（参数非法、组合不支持等）"""

    pass


class InvalidOptionError(ConfigurationError):
    """
    某个配置项的取值不合法（不在允许集合里）。
    """

    field: str
    value: Any
    allowed: tuple[Any, ...]

    def __init__(
        self,
        field: str,
        value: Any,
        allowed: Iterable[Any],
        *,
        prefix: str = "Invalid",
    ):
        """
        初始化异常。

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


class CallableParameterKindError(InvalidOptionError):
    """可调用对象参数 kind 不合法"""

    callable_name: str
    parameter_kind: Any
    valid_kinds: tuple[Any, ...]

    def __init__(
        self,
        callable_name: str,
        parameter_kind: Any,
        valid_kinds: Iterable[Any],
    ):
        """
        初始化异常。

        :param callable_name: 可调用对象名称
        :param parameter_kind: 实际参数 kind
        :param valid_kinds: 允许的参数 kind 集合
        """
        super().__init__(
            f"parameter kind of callable '{callable_name}'",
            parameter_kind,
            valid_kinds,
        )
        self.callable_name = callable_name
        self.parameter_kind = parameter_kind
        self.valid_kinds = self.allowed


# ==== 图结构 ====


class GraphStructureError(ConfigurationError):
    """图结构错误"""

    pass


class DuplicateNodeError(GraphStructureError):
    """重复的节点名称"""

    pass


class UnknownNodeError(GraphStructureError):
    """未知的节点名称"""

    pass


class NodeNotFoundError(GraphStructureError):
    """图中未找到指定节点"""

    pass


class InvalidStructureError(GraphStructureError):
    """无效的图结构输入（空节点列表、空网格、行长度不一致、节点数量不足等）"""

    pass


# ==== 运行时与生命周期 ====


class RuntimeStateError(CelestialFlowError):
    """运行时状态错误（如重复启动、未初始化等）"""

    pass


class InitializationError(RuntimeStateError):
    """初始化错误"""

    pass


class GraphManagedError(RuntimeStateError):
    """Stage 已被 Graph 管理，不应通过 standalone 路径启动。"""

    def __init__(
        self,
        message: str = "This stage is managed by a TaskGraph. Use TaskGraph.start()/start_async() or TaskGraph.run()/run_async() instead of calling stage.start() directly.",
    ) -> None:
        """
        初始化异常。

        :param message: 错误消息
        """
        super().__init__(message)


class CelestialFlowTimeoutError(CelestialFlowError, TimeoutError):
    """超时错误"""

    pass


class UnconsumedError(CelestialFlowError):
    """用于标记任务未消费的异常类"""

    pass


# ==== 外部服务与通信 ====


class RemoteWorkerError(CelestialFlowError):
    """远端 Worker（如 Go Worker）执行失败或返回异常状态时抛出。"""

    pass


class ReporterError(CelestialFlowError):
    """上报器错误"""

    pass


class PersistedError(CelestialFlowError):
    """从持久化层恢复出的错误摘要对象。"""

    error_type: str
    error_message: str

    def __init__(self, error_type: str, error_message: str) -> None:
        """
        初始化持久化错误对象。

        :param error_type: 错误类型名称
        :param error_message: 错误消息
        """
        super().__init__(error_message)
        self.error_type = error_type
        self.error_message = error_message

    def __str__(self) -> str:
        """返回 ``ErrorType(message)`` 形式的紧凑表示。"""
        return f"{self.error_type}({self.error_message})"


# ==== 任务与逻辑 ====


class TerminationMergeError(CelestialFlowError):
    """终止信号合并错误"""

    pass
