# persistence/util_jsonl.py
import json
import ast
from collections import defaultdict
from typing import Dict, Any, List, Optional

# ======== jsonl文件处理 ========


def load_jsonl_logs(
    path: str,
    start_seq: int = 1,
    keys: Optional[List[str]] = None,
) -> List[Dict]:
    """
    从 jsonl 文件中读取数据（可选择性读取字段）

    :param path: jsonl 文件路径
    :param start_seq: 起始序列号（行号，0-based）
    :param keys: 只保留这些键；None 表示保留全部
    :return: 从 start_seq 开始的 list[dict]
    """
    results: List[Dict] = []

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


def load_jsonl_grouped_by_keys(
    jsonl_path: str,
    group_keys: List[str],
    extract_fields: Optional[List[str]] = None,
    eval_fields: Optional[List[str]] = None,
    skip_if_missing: bool = True,
) -> Dict[str, List[Any]]:
    """
    加载 JSONL 文件内容并按多个 key 分组。

    :param jsonl_path: JSONL 文件路径
    :param group_keys: 用于分组的字段名列表（如 ['error', 'stage']）
    :param extract_fields: 要提取的字段名列表；为空时返回整个 item
    :param eval_fields: 哪些字段需要用 ast.literal_eval 解析
    :param skip_if_missing: 缺 key 是否跳过该条记录
    :return: 一个 {"(k1, k2)": [items]} 的字典
    """
    result_dict = defaultdict(list)

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                item = json.loads(line)
            except Exception:
                continue

            # 确保 group_keys 都存在
            if skip_if_missing and any(k not in item for k in group_keys):
                continue

            # 组合分组 key
            group_values = tuple(item.get(k, "") for k in group_keys)
            group_key = group_values if len(group_values) > 1 else group_values[0]

            # 字段反序列化（仅 eval_fields）
            if eval_fields:
                for key in eval_fields:
                    if key in item:
                        try:
                            item[key] = ast.literal_eval(item[key])
                        except Exception:
                            pass  # 解析失败不终止

            # 提取内容
            if extract_fields:
                if skip_if_missing and any(k not in item for k in extract_fields):
                    continue

                if len(extract_fields) == 1:
                    value = item[extract_fields[0]]
                else:
                    value = {k: item[k] for k in extract_fields if k in item}
            else:
                value = item

            result_dict[group_key].append(value)

    return dict(result_dict)


def load_task_by_stage(jsonl_path) -> Dict[str, list]:
    """
    加载错误记录，按 stage 分类
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path, group_keys=["stage"], extract_fields=["task"], eval_fields=["task"]
    )


def load_task_by_error(jsonl_path) -> Dict[str, list]:
    """
    加载错误记录，按 error 和 stage 分类
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path,
        group_keys=["error", "stage"],
        extract_fields=["task"],
        eval_fields=["task"],
    )
