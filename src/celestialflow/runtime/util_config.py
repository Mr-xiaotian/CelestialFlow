# runtime/util_config.py
from __future__ import annotations

import tomllib
from pathlib import Path

from .util_constant import LEVEL_DICT
from .util_errors import LogLevelError


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
                    raise LogLevelError(log_level)
                return log_level
            except tomllib.TOMLDecodeError:
                continue
    return "INFO"
