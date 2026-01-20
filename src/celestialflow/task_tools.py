import json, ast
import hashlib
import pickle
import networkx as nx
from networkx import is_directed_acyclic_graph
from itertools import zip_longest
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from multiprocessing import Queue as MPQueue
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any, List, Set, Optional

if TYPE_CHECKING:
    from .task_stage import TaskStage


# ========调用于task_graph.py========
def format_duration(seconds):
    """将秒数格式化为 HH:MM:SS 或 MM:SS（自动省略前导零）"""
    seconds = int(seconds)
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    else:
        return f"{minutes:02d}:{seconds:02d}"


def format_timestamp(timestamp) -> str:
    """将时间戳格式化为 YYYY-MM-DD HH:MM:SS"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def build_structure_graph(root_stages: List["TaskStage"]) -> List[Dict[str, Any]]:
    """
    从多个根节点构建任务链的 JSON 图结构

    :param root_stages: 根节点列表
    :return: 多棵任务图的 JSON 列表
    """
    visited_stages: Set[str] = set()
    graphs = []

    for root_stage in root_stages:
        graph = _build_structure_subgraph(root_stage, visited_stages)
        graphs.append(graph)

    return graphs


def _build_structure_subgraph(
    task_stage: "TaskStage", visited_stages: Set[str]
) -> Dict[str, Any]:
    """
    构建单个子图结构
    """
    stage_tag = task_stage.get_tag()
    node = {
        "stage_name": task_stage._name,
        "stage_mode": task_stage.stage_mode,
        "execution_mode": task_stage.execution_mode,
        "func_name": task_stage.func.__name__,
        "is_ref": False,
        "next_stages": [],
    }

    if stage_tag in visited_stages:
        node["is_ref"] = True
        return node

    visited_stages.add(stage_tag)

    for next_stage in task_stage.next_stages:
        child_node = _build_structure_subgraph(next_stage, visited_stages)
        node["next_stages"].append(child_node)

    return node


def format_structure_list_from_graph(
    root_roots: List[Dict] = None
) -> List[str]:
    """
    从多个 JSON 图结构生成格式化任务结构文本列表（带边框）

    :param root_roots: JSON 格式任务图根节点列表
    :return: 带边框的格式化字符串列表
    """

    def node_label(node: Dict) -> str:
        visited_note = " [Ref]" if node.get("is_ref") else ""
        N = node.get("stage_name", "?")      # N
        S = node.get("stage_mode", "?")      # S
        E = node.get("execution_mode", "?")  # E
        F = node.get("func_name", "?")       # F

        return (
            f"{N}::{F} "
            f"(S:{S}, E:{E})"
            f"{visited_note}"
        )

    # 只渲染“子节点”（有父节点）——保证一定画连接符
    def build_child_lines(node: Dict, prefix: str, is_last: bool) -> List[str]:
        connector = "╘-->" if is_last else "╞-->"
        lines = [f"{prefix}{connector}{node_label(node)}"]

        next_stages = node.get("next_stages", []) or []
        # 子节点的 prefix 取决于当前节点是不是 last：last -> 空白，否则竖线延续
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(next_stages):
            lines.extend(build_child_lines(child, child_prefix, i == len(next_stages) - 1))
        return lines

    # 专门处理 root：不画连接符，不产生祖先竖线
    def build_root_lines(root: Dict) -> List[str]:
        lines = [node_label(root)]
        next_stages = root.get("next_stages", []) or []
        for i, child in enumerate(next_stages):
            lines.extend(build_child_lines(child, "", i == len(next_stages) - 1))
        return lines

    all_lines = []
    for root in root_roots or []:
        if all_lines:
            all_lines.append("")  # 根之间留空行
        all_lines.extend(build_root_lines(root))

    if not all_lines:
        return ["+ No stages defined +"]

    max_length = max(len(line) for line in all_lines)
    content_lines = [f"| {line.ljust(max_length)} |" for line in all_lines]
    border = "+" + "-" * (max_length + 2) + "+"
    return [border] + content_lines + [border]


def cluster_by_value_sorted(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    """
    按值聚类，并确保按 value（键）升序排序

    :param input_dict: 输入字典
    :return: 聚类后的字典，键为值，值为键的列表
    """
    clusters = defaultdict(list)
    for key, val in input_dict.items():
        clusters[val].append(key)

    return dict(sorted(clusters.items()))  # ✅ 按键排序


# ========(图论分析)========
def format_networkx_graph(structure_graph: List[Dict[str, Any]]) -> nx.DiGraph:
    """
    将结构图（由 build_structure_graph 生成）转换为 networkx 有向图（DiGraph）

    :param structure_graph: JSON 格式的任务结构图，List[Dict]
    :return: 构建好的 networkx.DiGraph
    """
    G = nx.DiGraph()

    def add_node_and_edges(node: Dict[str, Any]):
        node_id = f'{node["stage_name"]}[{node["func_name"]}]'
        G.add_node(node_id, **{"mode": node.get("stage_mode")})

        for child in node.get("next_stages", []):
            child_id = f'{child["stage_name"]}[{child["func_name"]}]'
            G.add_edge(node_id, child_id)
            # 递归添加子节点
            add_node_and_edges(child)

    for root in structure_graph:
        add_node_and_edges(root)

    return G


def compute_node_levels(G: nx.DiGraph) -> Dict[str, int]:
    """
    计算 DAG 中每个节点的层级（最早执行阶段）
    前提：图必须是有向无环图（DAG）

    :param G: networkx 有向图（DiGraph）
    :return: dict[node] = level (int)
    """
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("该图不是 DAG，无法进行层级划分")

    level = {node: 0 for node in G.nodes}  # 初始层级为 0

    for node in nx.topological_sort(G):  # 按拓扑顺序遍历
        for succ in G.successors(node):
            level[succ] = max(level[succ], level[node] + 1)

    return level


# ========调用于task_types.py========
def make_hashable(obj) -> Any:
    """
    把 obj 转换成可哈希的形式。
    """
    if isinstance(obj, (tuple, list)):
        return tuple(make_hashable(e) for e in obj)
    elif isinstance(obj, dict):
        # dict 转换成 (key, value) 对的元组，且按 key 排序以确保哈希结果一致
        return tuple(
            sorted((make_hashable(k), make_hashable(v)) for k, v in obj.items())
        )
    elif isinstance(obj, set):
        # set 转换成排序后的 tuple
        return tuple(sorted(make_hashable(e) for e in obj))
    else:
        # 基本类型直接返回
        return


def object_to_str_hash(obj) -> str:
    """
    将任意对象转换为 MD5 字符串。

    :param obj: 任意对象
    :return: MD5 字符串
    """
    obj_bytes = pickle.dumps(obj)  # 序列化对象
    return hashlib.md5(obj_bytes).hexdigest()


# ========公共函数========
def cleanup_mpqueue(queue: MPQueue):
    """
    清理队列
    """
    queue.close()
    queue.join_thread()  # 确保队列的后台线程正确终止


def format_repr(obj: Any, max_length: int) -> str:
    """
    将对象格式化为字符串，自动转义换行、截断超长文本。

    :param obj: 任意对象
    :param max_length: 显示的最大字符数（超出将被截断）
    :return: 格式化字符串
    """
    obj_str = str(obj).replace("\\", "\\\\").replace("\n", "\\n")
    if max_length <= 0 or len(obj_str) <= max_length:
        return obj_str

    # 截断逻辑（前 2/3 + ... + 后 1/3）
    segment_len = max(1, max_length // 3)

    first_part = obj_str[: segment_len * 2]
    last_part = obj_str[-segment_len:]

    return f"{first_part}...{last_part}"


def format_table(
    data: list,
    row_names: list = None,
    column_names: list = None,
    index_header: str = "#",
    fill_value: str = "N/A",
    align: str = "left",
) -> str:
    """
    格式化表格数据为字符串(CelestialVault.TextTools中同名函数的简化版)。
    """

    def _generate_excel_column_names(n: int, start_index: int = 0) -> list[str]:
        """
        生成 Excel 风格列名（A, B, ..., Z, AA, AB, ...）
        支持从指定起始索引开始生成。
        """
        names = []
        for i in range(start_index, start_index + n):
            name = ""
            x = i
            while True:
                name = chr(ord("A") + (x % 26)) + name
                x = x // 26 - 1
                if x < 0:
                    break
            names.append(name)
        return names

    if not data:
        return "表格数据为空！"

    # 计算列数
    max_cols = max(map(len, data))

    # 生成列名
    if column_names is None:
        column_names = _generate_excel_column_names(max_cols)
    elif len(column_names) < max_cols:
        start = len(column_names)  # 从当前列名数量继续命名
        column_names.extend(
            _generate_excel_column_names(max_cols - len(column_names), start)
        )

    # 生成行名
    if row_names is None:
        row_names = range(len(data))
    elif len(row_names) < len(data):
        row_names.extend([i for i in range(len(row_names), len(data))])

    # 添加行号列
    column_names = [index_header] + column_names
    num_columns = len(column_names)

    # 处理行号
    formatted_data = []
    for i, row in enumerate(data):
        row_label = row_names[i] if row_names else i
        formatted_data.append([row_label] + list(row))

    # 统一填充数据行，确保所有行长度一致
    formatted_data = zip_longest(*formatted_data, fillvalue=fill_value)
    formatted_data = list(zip(*formatted_data))  # 转置回来

    # 计算每列的最大宽度
    col_widths = [
        max(len(str(item)) for item in col)
        for col in zip(column_names, *formatted_data)
    ]

    # 选择对齐方式
    align_funcs = {
        "left": lambda text, width: f"{text:<{width}}",
        "right": lambda text, width: f"{text:>{width}}",
        "center": lambda text, width: f"{text:^{width}}",
    }
    align_func = align_funcs.get(align, align_funcs["left"])  # 默认左对齐

    # 生成表格
    separator = "+" + "+".join(["-" * (width + 2) for width in col_widths]) + "+"
    header = (
        "| "
        + " | ".join(
            [
                f"{align_func(name, col_widths[i])}"
                for i, name in enumerate(column_names)
            ]
        )
        + " |"
    )

    # 生成行
    rows_list = []
    for row in formatted_data:
        rows_list.append(
            "| "
            + " | ".join(
                [
                    f"{align_func(str(row[i]), col_widths[i])}"
                    for i in range(num_columns)
                ]
            )
            + " |"
        )
    rows = "\n".join(rows_list)

    # 拼接表格
    table = f"{separator}\n{header}\n{separator}\n{rows}\n{separator}"
    return table


# ======== 处理jsonl文件 ========
def append_jsonl_log(log_data: dict, file_path: str, logger=None):
    """
    将日志字典写入指定目录下的 JSONL 文件。

    :param log_data: 要写入的日志项（字典）
    :param start_time: 运行开始时间，用于构造路径
    :param base_path: 基础路径，例如 './fallback'
    :param prefix: 文件名前缀，例如 'realtime_errors'
    :param logger: 可选的日志对象用于记录失败信息
    """
    try:
        file_path: Path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    except Exception as e:
        if logger:
            logger._log("WARNING", f"[Persist] 写入日志失败: {e}")


def append_jsonl_logs(log_items: Iterable[dict], file_path: str, logger=None):
    """
    将多条日志一次性写入 JSONL 文件（batch 追加）。

    :param log_items: Iterable[dict]，每个元素写成一行 JSON
    :param file_path: JSONL 文件路径
    :param logger: 可选日志对象
    """
    try:
        if not isinstance(log_items, Iterable):
            raise TypeError("log_items must be an iterable of dict")

        file_path: Path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            for item in log_items:
                if not isinstance(item, dict):
                    raise TypeError(f"each log item must be dict, got {type(item)}")
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        if logger:
            logger._log("WARNING", f"[Persist] 批量写入日志失败: {e}")


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