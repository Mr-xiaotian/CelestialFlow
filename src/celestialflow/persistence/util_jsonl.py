# persistence/util_jsonl.py
from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..runtime.util_types import PersistedErrorRecord

# ======== jsonl文件处理 ========


def _parse_error_record(item: dict[str, Any]) -> PersistedErrorRecord:
    """
    从 JSONL 记录中解析错误记录对象

    :param item: JSONL 中的一条错误记录
    :return: 结构化错误记录
    """
    ts = item.get("ts")
    stage = item.get("stage", "")

    error_id = item.get("error_id")
    error_type = str(item.get("error_type") or "")
    error_message = str(item.get("error_message") or "")

    return PersistedErrorRecord(
        ts=ts,
        stage=stage,
        error_id=error_id,
        error_type=error_type,
        error_message=error_message,
    )


def parse_jsonl_value(val: Any) -> Any:
    """
    智能解析 JSONL 字段值

    :param val: 原始字段值
    :return: 解析后的值
    """
    if isinstance(val, str):
        try:
            parsed: Any = ast.literal_eval(val)
            return tuple(parsed) if isinstance(parsed, list | tuple) else parsed  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        except (ValueError, SyntaxError):
            return val
    if isinstance(val, list | tuple):
        return tuple(val)  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return val


def load_jsonl_logs(
    path: str,
    start_seq: int = 1,
    keys: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    从 jsonl 文件中读取数据（可选择性读取字段）

    :param path: jsonl 文件路径
    :param start_seq: 跳过前 N 行（默认跳过第 0 行的元信息行），默认 1
    :param keys: 只保留这些键；None 表示保留全部，默认 None
    :return: 从 start_seq 开始的 list[dict]
    """
    results: list[dict[str, Any]] = []

    if start_seq < 0:
        start_seq = 0

    keyset = set(keys) if keys else None

    with open(path, encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx < start_seq:
                continue

            line = line.strip()
            if not line:
                continue

            try:
                obj: dict[str, Any] = json.loads(line)

                if keyset is not None:
                    obj = {k: obj.get(k) for k in keyset}

                results.append(obj)

            except json.JSONDecodeError:
                # 脏行直接跳过，日志系统讲究"活着"
                continue

    return results


def load_jsonl_by_key(
    jsonl_path: str | Path, extract_key: str = "stage", extract_value: str = "task"
) -> dict[str, list[Any]]:
    """
    按指定 key 分组加载 jsonl 文件中的值

    :param jsonl_path: jsonl 文件路径
    :param extract_key: 分组依据的字段名，默认 "stage"
    :param extract_value: 提取的值字段名，默认 "task"
    :return: {key_value: [parsed_values]}
    """
    result_dict: defaultdict[str, list[Any]] = defaultdict(list)

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            item: dict[str, Any] = json.loads(line)

            if extract_key not in item or extract_value not in item:
                continue

            key: Any = item[extract_key]
            val: Any = item[extract_value]
            value: Any = parse_jsonl_value(val)

            result_dict[key].append(value)

    return dict(result_dict)


def load_jsonl_grouped_by_keys(
    jsonl_path: str | Path,
    group_keys: list[str],
    extract_field: str,
) -> dict[tuple[str, ...], list[Any]]:
    """
    加载 JSONL 文件内容并按多个 key 分组。

    :param jsonl_path: JSONL 文件路径
    :param group_keys: 用于分组的字段名列表（如 ['error', 'stage']）
    :param extract_field: 要提取的字段名
    :return: 一个 {(k1, k2): [items]} 的字典（键为 tuple）
    """
    result_dict: defaultdict[tuple[str, ...], list[Any]] = defaultdict(list)

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            item: dict[str, Any] = json.loads(line)

            if any(k not in item for k in group_keys):
                continue

            # 组合分组 key
            group_values = tuple(item.get(k, "") for k in group_keys)
            group_key = group_values

            value: Any = parse_jsonl_value(item[extract_field])

            result_dict[group_key].append(value)

    return dict(result_dict)


def load_task_by_stage(jsonl_path: str | Path) -> dict[str, list[Any]]:
    """
    加载错误记录，按 stage 分类

    :param jsonl_path: JSONL 文件路径
    :return: {stage_name: [task_list]}
    """
    return load_jsonl_by_key(jsonl_path, extract_key="stage", extract_value="task")


def load_task_by_error(jsonl_path: str | Path) -> dict[tuple[str, ...], list[Any]]:
    """
    加载错误记录，按 error_type 和 stage 分类

    :param jsonl_path: JSONL 文件路径
    :return: {(error_type, stage): [task_list]}
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path, group_keys=["error_type", "stage"], extract_field="task"
    )


def load_task_error_pairs(
    jsonl_path: str | Path,
) -> list[tuple[Any, PersistedErrorRecord]]:
    """
    加载错误记录，返回 (task, error) pair 列表

    :param jsonl_path: JSONL 文件路径
    :return: [(task, error), ...]
    """
    result: list[tuple[Any, PersistedErrorRecord]] = []

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item: Any = json.loads(line)
            except json.JSONDecodeError:
                continue

            has_error = any(key in item for key in ("error_type", "error_message"))
            if "task" not in item or not has_error:
                continue

            task: Any = parse_jsonl_value(item["task"])
            error: PersistedErrorRecord = _parse_error_record(item)
            result.append((task, error))

    return result
