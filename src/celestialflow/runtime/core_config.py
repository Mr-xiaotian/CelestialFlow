# runtime/core_config.py
"""运行期配置对象。

集中定义由运行入口（``run`` / ``run_async`` / ``restore_db``）显式传入的
配置类型，避免在运行期从宿主项目的 ``pyproject.toml`` 隐式读取配置。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from urllib.parse import urlsplit

from .util_constant import LEVEL_DICT
from .util_errors import ConfigurationError, InvalidOptionError

DEFAULT_REPORT_URL = "http://127.0.0.1:5005"
"""``ReportConfig`` 未显式指定地址时使用的默认上报地址。"""


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


@dataclass(frozen=True, slots=True)
class ReportConfig:
    """
    远程上报配置。

    只要把该对象传给图运行入口即表示启用上报；不传（``None``）表示关闭。
    对象在构造时完成校验，因此非法地址会在启动运行期资源之前抛出错误。

    :param url: 上报服务基础地址，必须为 ``http`` / ``https``；末尾的 ``/``
        会被去掉，以便与各上报端点拼接
    :raises ConfigurationError: ``url`` 不是字符串、为空或不是合法的
        ``http`` / ``https`` 地址时
    """

    url: str = DEFAULT_REPORT_URL

    def __post_init__(self) -> None:
        """
        校验并规范化上报地址。

        :raises ConfigurationError: ``url`` 不是字符串、为空或不是合法的
            ``http`` / ``https`` 地址时
        """
        raw_url = cast(object, self.url)
        if not isinstance(raw_url, str):
            raise ConfigurationError(f"report url must be a string, got {raw_url!r}.")

        url = raw_url.strip().rstrip("/")
        if not url:
            raise ConfigurationError("report url must not be empty.")

        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ConfigurationError(
                f"report url must be an http(s) address, got {self.url!r}."
            )

        object.__setattr__(self, "url", url)
