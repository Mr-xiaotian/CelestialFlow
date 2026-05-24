# persistence/util_jsonl.py
from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from ..runtime.util_types import PersistedErrorRecord

# ======== jsonl文件处理 ========


def _split_error_repr(error_repr: str) -> tuple[str, str]:
    """
    从旧版错误字符串中拆分错误类型和消息

    :param error_repr: 错误展示字符串
    :return: (error_type, error_message)
    """
    if not error_repr:
        return ("Exception", "")
    if "(" in error_repr and error_repr.endswith(")"):
        error_type, error_message = error_repr.split("(", 1)
        return (error_type or "Exception", error_message[:-1])
    return ("Exception", error_repr)


def _parse_error_record(item: dict[str, Any]) -> PersistedErrorRecord:  # pyright: ignore[reportExplicitAny]
    """
    从 JSONL 记录中解析错误记录对象

    :param item: JSONL 中的一条错误记录
    :return: 结构化错误记录
    """
    error_repr = str(item.get("error_repr") or item.get("error") or "")
    legacy_error_type, legacy_error_message = _split_error_repr(error_repr)

    error_id = item.get("error_id")
    ts = item.get("ts")

    return PersistedErrorRecord(
        error_type=str(item.get("error_type") or legacy_error_type),
        error_message=str(item.get("error_message") or legacy_error_message),
        error_repr=error_repr,
        stage=str(item.get("stage") or ""),
        error_id=error_id if isinstance(error_id, int) else None,
        timestamp=str(item.get("timestamp") or ""),
        ts=ts if isinstance(ts, (int, float)) else None,
    )


def parse_jsonl_value(val: Any) -> Any:  # pyright: ignore[reportExplicitAny, reportAny]
    """
    智能解析 JSONL 字段值

    :param val: 原始字段值
    :return: 解析后的值
    """
    if isinstance(val, str):
        try:
            parsed: Any = ast.literal_eval(val)  # pyright: ignore[reportExplicitAny, reportAny]
            return tuple(parsed) if isinstance(parsed, (list, tuple)) else parsed  # type: ignore[return-value]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
        except (ValueError, SyntaxError):
            return val
    if isinstance(val, (list, tuple)):
        return tuple(val)  # type: ignore[return-value]  # pyright: ignore[reportUnknownVariableType, reportUnknownArgumentType]
    return val  # pyright: ignore[reportAny]


def load_jsonl_logs(
    path: str,
    start_seq: int = 1,
    keys: list[str] | None = None,
) -> list[dict[str, Any]]:  # pyright: ignore[reportExplicitAny]
    """
    从 jsonl 文件中读取数据（可选择性读取字段）

    :param path: jsonl 文件路径
    :param start_seq: 跳过前 N 行（默认跳过第 0 行的元信息行），默认 1
    :param keys: 只保留这些键；None 表示保留全部，默认 None
    :return: 从 start_seq 开始的 list[dict]
    """
    results: list[dict[str, Any]] = []  # pyright: ignore[reportExplicitAny]

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
                obj: dict[str, Any] = json.loads(line)  # pyright: ignore[reportExplicitAny, reportAny]

                if keyset is not None:
                    obj = {k: obj.get(k) for k in keyset}

                results.append(obj)

            except json.JSONDecodeError:
                # 脏行直接跳过，日志系统讲究"活着"
                continue

    return results


def load_jsonl_by_key(
    jsonl_path: str | Path, extract_key: str = "stage", extract_value: str = "task"
) -> dict[str, list[Any]]:  # pyright: ignore[reportExplicitAny]
    """
    按指定 key 分组加载 jsonl 文件中的值

    :param jsonl_path: jsonl 文件路径
    :param extract_key: 分组依据的字段名，默认 "stage"
    :param extract_value: 提取的值字段名，默认 "task"
    :return: {key_value: [parsed_values]}
    """
    result_dict: defaultdict[str, list[Any]] = defaultdict(list)  # pyright: ignore[reportExplicitAny]

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item: dict[str, Any] = json.loads(line)  # pyright: ignore[reportExplicitAny, reportAny]

            if extract_key not in item or extract_value not in item:
                continue

            key: Any = item[extract_key]  # pyright: ignore[reportExplicitAny, reportAny]
            val: Any = item[extract_value]  # pyright: ignore[reportExplicitAny, reportAny]
            value: Any = parse_jsonl_value(val)  # pyright: ignore[reportExplicitAny, reportAny]

            result_dict[key].append(value)

    return dict(result_dict)


def load_jsonl_grouped_by_keys(
    jsonl_path: str | Path,
    group_keys: list[str],
    extract_field: str,
) -> dict[tuple[str, ...], list[Any]]:  # pyright: ignore[reportExplicitAny]
    """
    加载 JSONL 文件内容并按多个 key 分组。

    :param jsonl_path: JSONL 文件路径
    :param group_keys: 用于分组的字段名列表（如 ['error', 'stage']）
    :param extract_field: 要提取的字段名
    :return: 一个 {(k1, k2): [items]} 的字典（键为 tuple）
    """
    result_dict: defaultdict[tuple[str, ...], list[Any]] = defaultdict(list)  # pyright: ignore[reportExplicitAny]

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            item: dict[str, Any] = json.loads(line)  # pyright: ignore[reportExplicitAny, reportAny]

            if any(k not in item for k in group_keys):
                continue

            # 组合分组 key
            group_values = tuple(item.get(k, "") for k in group_keys)
            group_key = group_values

            value: Any = parse_jsonl_value(item[extract_field])  # pyright: ignore[reportExplicitAny, reportAny]

            result_dict[group_key].append(value)

    return dict(result_dict)


def load_task_by_stage(jsonl_path: str | Path) -> dict[str, list[Any]]:  # pyright: ignore[reportExplicitAny]
    """
    加载错误记录，按 stage 分类

    :param jsonl_path: JSONL 文件路径
    :return: {stage_name: [task_list]}
    """
    return load_jsonl_by_key(jsonl_path, extract_key="stage", extract_value="task")


def load_task_by_error(jsonl_path: str | Path) -> dict[tuple[str, ...], list[Any]]:  # pyright: ignore[reportExplicitAny]
    """
    加载错误记录，按 error 和 stage 分类

    :param jsonl_path: JSONL 文件路径
    :return: {(error, stage): [task_list]}
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path, group_keys=["error", "stage"], extract_field="task"
    )


def load_task_error_pairs(
    jsonl_path: str | Path,
) -> list[tuple[Any, PersistedErrorRecord]]:  # pyright: ignore[reportExplicitAny]
    """
    加载错误记录，返回 (task, error) pair 列表

    :param jsonl_path: JSONL 文件路径
    :return: [(task, error), ...]
    """
    result: list[tuple[Any, PersistedErrorRecord]] = []  # pyright: ignore[reportExplicitAny]

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                item: Any = json.loads(line)  # pyright: ignore[reportExplicitAny, reportAny]
            except json.JSONDecodeError:
                continue

            if "task" not in item or "error" not in item:
                continue

            task: Any = parse_jsonl_value(item["task"])  # pyright: ignore[reportExplicitAny, reportAny]
            error: PersistedErrorRecord = _parse_error_record(item)  # pyright: ignore[reportAny]
            result.append((task, error))

    return result
