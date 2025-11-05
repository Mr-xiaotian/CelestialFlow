import json, ast
import hashlib
import pickle
import networkx as nx
from networkx import is_directed_acyclic_graph
from collections import defaultdict
from datetime import datetime
from multiprocessing import Queue as MPQueue
from asyncio import Queue as AsyncQueue
from queue import Queue as ThreadQueue
from pathlib import Path
from queue import Empty
from asyncio import QueueEmpty as AsyncQueueEmpty
from typing import TYPE_CHECKING, Dict, Any, List, Set, Optional

if TYPE_CHECKING:
    from .task_manage import TaskManager


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


def build_structure_graph(root_stages: List["TaskManager"]) -> List[Dict[str, Any]]:
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
    task_manager: "TaskManager", visited_stages: Set[str]
) -> Dict[str, Any]:
    """
    构建单个子图结构
    """
    stage_tag = task_manager.get_stage_tag()
    node = {
        "stage_name": task_manager.stage_name,
        "stage_mode": task_manager.stage_mode,
        "func_name": task_manager.func.__name__,
        "visited": False,
        "next_stages": [],
    }

    if stage_tag in visited_stages:
        node["visited"] = True
        return node

    visited_stages.add(stage_tag)

    for next_stage in task_manager.next_stages:
        child_node = _build_structure_subgraph(next_stage, visited_stages)
        node["next_stages"].append(child_node)

    return node


def format_structure_list_from_graph(
    root_roots: List[Dict] = None, indent=0
) -> List[str]:
    """
    从多个 JSON 图结构生成格式化任务结构文本列表（带边框）

    :param root_roots: JSON 格式任务图根节点列表
    :param indent: 当前缩进级别
    :return: 带边框的格式化字符串列表
    """

    def build_lines(node: Dict, current_indent: int) -> List[str]:
        lines = []
        visited_note = " [Visited]" if node.get("visited") else ""
        line = f"{node['stage_name']} (stage_mode: {node['stage_mode']}, func: {node['func_name']}){visited_note}"
        lines.append(line)

        for child in node.get("next_stages", []):
            sub_lines = build_lines(child, current_indent + 2)
            arrow_prefix = "  " * current_indent + "╘-->"
            sub_lines[0] = f"{arrow_prefix}{sub_lines[0]}"
            lines.extend(sub_lines)

        return lines

    all_lines = []
    for root in root_roots or []:
        if all_lines:
            all_lines.append("")  # 根之间留空行
        all_lines.extend(build_lines(root, indent))

    if not all_lines:
        return ["+ No stages defined +"]

    max_length = max(len(line) for line in all_lines)
    content_lines = [f"| {line.ljust(max_length)} |" for line in all_lines]
    border = "+" + "-" * (max_length + 2) + "+"
    return [border] + content_lines + [border]


def append_jsonl_log(
    log_data: dict, start_time: float, base_path: str, prefix: str, logger=None
):
    """
    将日志字典写入指定目录下的 JSONL 文件。

    :param log_data: 要写入的日志项（字典）
    :param start_time: 运行开始时间，用于构造路径
    :param base_path: 基础路径，例如 './fallback'
    :param prefix: 文件名前缀，例如 'realtime_errors'
    :param logger: 可选的日志对象用于记录失败信息
    """
    try:
        date_str = datetime.fromtimestamp(start_time).strftime("%Y-%m-%d")
        time_str = datetime.fromtimestamp(start_time).strftime("%H-%M-%S-%f")[:-3]
        file_path = Path(base_path) / date_str / f"{prefix}({time_str}).jsonl"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    except Exception as e:
        if logger:
            logger._log("WARNING", f"[Persist] 写入日志失败: {e}")


def cluster_by_value_sorted(input_dict: Dict[str, int]) -> Dict[int, List[str]]:
    """
    按值聚类，并确保按 value（键）升序排序
    """
    from collections import defaultdict

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

    返回: dict[node] = level (int)
    """
    if not nx.is_directed_acyclic_graph(G):
        raise ValueError("该图不是 DAG，无法进行层级划分")

    level = {node: 0 for node in G.nodes}  # 初始层级为 0

    for node in nx.topological_sort(G):  # 按拓扑顺序遍历
        for succ in G.successors(node):
            level[succ] = max(level[succ], level[node] + 1)

    return level


# ========调用于task_manage.py========
def is_queue_empty(q: ThreadQueue) -> bool:
    """
    判断队列是否为空
    """
    try:
        item = q.get_nowait()
        q.put(item)  # optional: put it back
        return False
    except Empty:
        return True


async def is_queue_empty_async(q: AsyncQueue) -> bool:
    """
    判断队列是否为空
    """
    try:
        item = q.get_nowait()
        await q.put(item)  # ✅ 修复点
        return False
    except AsyncQueueEmpty:
        return True


def are_queues_empty(queues: List[ThreadQueue]) -> bool:
    """
    判断多个同步队列是否都为空。
    所有队列都为空才返回 True。
    """
    for q in queues:
        if not is_queue_empty(q):
            return False
    return True


async def are_queues_empty_async(queues: List[AsyncQueue]) -> bool:
    """
    判断多个异步队列是否都为空。
    所有队列都为空才返回 True。
    """
    for q in queues:
        if not await is_queue_empty_async(q):
            return False
    return True


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
    first_part = obj_str[: int(max_length * 2 / 3)]
    last_part = obj_str[-int(max_length / 3) :]
    return f"{first_part}...{last_part}"


def object_to_str_hash(obj) -> str:
    """
    将任意对象转换为 MD5 字符串。
    """
    obj_bytes = pickle.dumps(obj)  # 序列化对象
    return hashlib.md5(obj_bytes).hexdigest()


# ========公共函数========
def make_hashable(obj):
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
        return obj


def cleanup_mpqueue(queue: MPQueue):
    """
    清理队列
    """
    queue.close()
    queue.join_thread()  # 确保队列的后台线程正确终止


# ========外部调用========
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
            group_key = (
                f"({', '.join(map(str, group_values))})"
                if len(group_values) > 1
                else group_values[0]
            )

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


def load_task_by_stage(jsonl_path):
    """
    加载错误记录，按 stage 分类
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path, group_keys=["stage"], extract_fields=["task"], eval_fields=["task"]
    )


def load_task_by_error(jsonl_path):
    """
    加载错误记录，按 error 和 stage 分类
    """
    return load_jsonl_grouped_by_keys(
        jsonl_path,
        group_keys=["error", "stage"],
        extract_fields=["task"],
        eval_fields=["task"],
    )
