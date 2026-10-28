# runtime/util_log_level.py
"""日志级别校验工具。

仅提供运行入口内部使用的级别规范化，不属于对外配置 API。
"""

from __future__ import annotations

from typing import cast

from .util_constant import LEVEL_DICT
from .util_errors import ConfigurationError, InvalidOptionError


def normalize_log_level(log_level: str) -> str:
    """
    校验并规范化日志级别。

    级别名不区分大小写，首尾空白会被忽略；规范化结果为
    :data:`~celestialflow.runtime.util_constant.LEVEL_DICT` 中的大写键名。

    :param log_level: 待校验的日志级别
    :return: 规范化后的日志级别（大写）
    :rtype: str
    :raises ConfigurationError: ``log_level`` 不是字符串时
    :raises InvalidOptionError: ``log_level`` 不在允许的级别集合中时
    """
    raw = cast(object, log_level)
    if not isinstance(raw, str):
        raise ConfigurationError(f"log level must be a string, got {raw!r}.")

    normalized = raw.strip().upper()
    if normalized not in LEVEL_DICT:
        raise InvalidOptionError("log level", log_level, tuple(LEVEL_DICT.keys()))
    return normalized
