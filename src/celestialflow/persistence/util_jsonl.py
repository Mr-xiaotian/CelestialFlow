# persistence/util_jsonl.py
import ast
import json
from collections import defaultdict
from typing import Any, Optional

# ======== jsonl文件处理 ========


def parse_jsonl_value(val: Any) -> Any:
    """
    智能解析 JSONL 字段值

    :param val: 原始字段值
    :return: 解析后的值
    """
    if isinstance(val, str):
        try:
            parsed = ast.literal_eval(val)
            return tuple(parsed) if isinstance(parsed, (list, tuple)) else parsed
        except (ValueError, SyntaxError):
            return val
    if isinstance(val, (list, tuple)):
        return tuple(val)
    return val


def load_jsonl_logs(
    path: str,
    start_seq: int = 1,
    keys: Optional[list[str]] = None,
) -> list[dict]:
    """
    从 jsonl 文件中读取数据（可选择性读取字段）

    :param path: jsonl 文件路径
    :param start_seq: 起始序列号（行号，0-based）
    :param keys: 只保留这些键；None 表示保留全部
    :return: 从 start_seq 开始的 list[dict]
    """
    results: list[dict] = []

    if start_seq < 0:
        start_seq = 0

    keyset = set(keys) if keys else None

    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx < start_seq:
                continue

            line = line.strip()
            if not line:
                continue

            try:
                obj: dict = json.loads(line)

                if keyset is not None:
                    obj = {k: obj.get(k) for k in keyset}

                results.append(obj)

            except json.JSONDecodeError:
                # 脏行直接跳过，日志系统讲究“活着”
                continue

    return results


def load_jsonl_by_key(
    jsonl_path: str, extract_key: str = "stage", extract_value: str = "task"
) -> dict[str, list]:
    """ """
    result_dict = defaultdict(list)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            if extract_key not in item or extract_value not in item:
                continue

            key = item[extract_key]
            val = item[extract_value]
            value = parse_jsonl_value(val)

            result_dict[key].append(value)

    return dict(result_dict)


def load_jsonl_grouped_by_keys(
    jsonl_path: str,
    group_keys: list[str],
    extract_field: str,
) -> dict[tuple[str], list[Any]]:
    """
    加载 JSONL 文件内容并按多个 key 分组。

    :param jsonl_path: JSONL 文件路径
    :param group_keys: 用于分组的字段名列表（如 ['error', 'stage']）
    :param extract_field: 要提取的字段名
    :return: 一个 {"(k1, k2)": [items]} 的字典
    """
    result_dict = defaultdict(list)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item = json.loads(line)

            if any(k not in item for k in group_keys):
                continue

            # 组合分组 key
            group_values = tuple(item.get(k, "") for k in group_keys)
            group_key = group_values

            value = parse_jsonl_value(item[extract_field])

            result_dict[group_key].append(value)

    return dict(result_dict)


def load_task_by_stage(jsonl_path) -> dict[str, list]:
    """
    加载错误记录，按 stage 分类

    :param jsonl_path: JSONL 文件路径
    """
    return load_jsonl_by_key(jsonl_path, extract_key="stage", extract_value="task")


def load_task_by_error(jsonl_path) -> dict[tuple[str], list[Any]]:
    """
    加载错误记录，按 error 和 stage 分类

        :param jsonl_path: JSONL 文件路径
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path, group_keys=["error", "stage"], extract_field="task"
    )


def load_task_error_pairs(jsonl_path: str) -> list[tuple[Any, Exception]]:
    """
    加载错误记录，返回 (task, error) pair 列表

    :param jsonl_path: JSONL 文件路径
    :return: [(task, error), ...]
    """
    result: list[tuple[Any, Exception]] = []

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue

            if "task" not in item or "error" not in item:
                continue

            task = parse_jsonl_value(item["task"])
            error = Exception(str(item["error"]))
            result.append((task, error))

    return result
