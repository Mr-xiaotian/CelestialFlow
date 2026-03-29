# web/util_config.py
import os
import json


def load_config(config_path: str) -> dict:
    """从指定路径加载并校验前端配置，返回序列化后的字典。"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data


def save_config(config: dict, config_path: str) -> bool:
    """将前端配置保存到 config.json，返回是否成功。"""
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error: Failed to save config: {e}")
        return False