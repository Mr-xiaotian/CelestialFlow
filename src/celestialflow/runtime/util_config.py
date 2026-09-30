# runtime/util_config.py
from __future__ import annotations

import tomllib
from pathlib import Path

from .util_constant import LEVEL_DICT
from .util_errors import ConfigurationError, InvalidOptionError

DEFAULT_REPORT_URL = "http://127.0.0.1:5005"
"""``report_url`` 未配置时使用的默认上报地址。"""


def load_log_level_from_pyproject() -> str:
    """
    从项目级 ``pyproject.toml`` 的 ``[tool.celestialflow]`` 节读取 ``log_level``。

    从当前工作目录开始向上搜索，未找到时返回 ``"INFO"``。

    :return: 日志级别字符串（大写）
    :rtype: str
    """
    current_dir = Path.cwd()
    for parent in [current_dir, *current_dir.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text("utf-8"))
                level = (
                    data.get("tool", {})
                    .get("celestialflow", {})
                    .get("log_level", "INFO")
                )

                log_level = str(level).upper()
                if log_level not in LEVEL_DICT:
                    raise InvalidOptionError(
                        "log level", log_level, tuple(LEVEL_DICT.keys())
                    )
                return log_level
            except tomllib.TOMLDecodeError:
                continue
    return "INFO"


def load_report_url_from_pyproject() -> str:
    """
    从项目级 ``pyproject.toml`` 的 ``[tool.celestialflow]`` 节读取 ``report_url``。

    从当前工作目录开始向上搜索，未找到对应配置时返回默认地址
    :data:`DEFAULT_REPORT_URL`。

    :return: 上报服务地址
    :rtype: str
    """
    current_dir = Path.cwd()
    for parent in [current_dir, *current_dir.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text("utf-8"))
                celestialflow = data.get("tool", {}).get("celestialflow", {})
                url = celestialflow.get("report_url", DEFAULT_REPORT_URL)
                return str(url)
            except tomllib.TOMLDecodeError:
                continue
    return DEFAULT_REPORT_URL


def load_if_report_from_pyproject() -> bool:
    """
    从项目级 ``pyproject.toml`` 的 ``[tool.celestialflow]`` 节读取
    ``if_report``。

    从当前工作目录开始向上搜索，未找到对应配置时返回 ``False``。上报开关与
    上报地址解耦：只有显式配置为 ``true`` 时才启用上报，``report_url`` 的存在
    本身不再触发上报。

    :return: 是否启用上报；未配置时为 ``False``
    :rtype: bool
    :raises ConfigurationError: 配置值不是布尔时
    """
    current_dir = Path.cwd()
    for parent in [current_dir, *current_dir.parents]:
        pyproject = parent / "pyproject.toml"
        if pyproject.exists():
            try:
                data = tomllib.loads(pyproject.read_text("utf-8"))
                celestialflow = data.get("tool", {}).get("celestialflow", {})
                raw = celestialflow.get("if_report")
                if raw is None:
                    return False
                if not isinstance(raw, bool):
                    raise ConfigurationError(
                        f"if_report must be a boolean, got {raw!r}."
                    )
                return raw
            except tomllib.TOMLDecodeError:
                continue
    return False
