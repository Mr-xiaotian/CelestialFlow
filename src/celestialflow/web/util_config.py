# web/util_config.py
import json
import os
from typing import Any

from ..runtime.util_errors import ConfigurationError


def load_config(config_path: str) -> dict[str, Any]:
    """
    从指定路径加载并校验前端配置，返回序列化后的字典。

    :param config_path: 配置文件路径
    :return: 配置字典
    :raises ConfigurationError: 配置文件不存在时抛出
    """
    if not os.path.exists(config_path):
        raise ConfigurationError(f"config file not found: {config_path}")
    with open(config_path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    return data


def save_config(config: dict[str, Any], config_path: str) -> bool:
    """
    将前端配置保存到 config.json，返回是否成功。

    :param config: 配置字典
    :param config_path: 配置文件路径
    :return: 是否保存成功
    """
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: Failed to save config: {e}")
        return False
