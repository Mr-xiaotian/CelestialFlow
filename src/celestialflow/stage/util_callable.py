# stage/util_callable.py
import inspect
from collections.abc import Callable
from typing import Any

from ..runtime.util_errors import CallableParameterKindError


def validate_executor_func_signature(func: Callable[..., Any]) -> int:
    """
    验证执行器函数的参数 kind 是否符合要求，并返回参数数量。

    :param func: 执行器函数
    :return: 参数数量
    """
    signature = inspect.signature(func)
    parameters = list(signature.parameters.values())
    
    valid_kinds = (
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
    )
    for parameter in parameters:
        if parameter.kind not in valid_kinds:
            raise CallableParameterKindError(
                getattr(func, "__name__", type(func).__name__),
                parameter.kind,
                valid_kinds,
            )

    return len(parameters)
