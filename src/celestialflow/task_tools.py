import hashlib
import pickle
import networkx as nx
from networkx import is_directed_acyclic_graph
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, Any, List, Set

if TYPE_CHECKING:
    from .stage import TaskStage


# ======== 处理图结构 ========
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
        **task_stage.get_summary(),
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


def format_structure_list_from_graph(root_roots: List[Dict] = None) -> List[str]:
    """
    从多个 JSON 图结构生成格式化任务结构文本列表（带边框）

    :param root_roots: JSON 格式任务图根节点列表
    :return: 带边框的格式化字符串列表
    """

    def node_label(node: Dict) -> str:
        visited_note = " [Ref]" if node.get("is_ref") else ""
        N = node.get("actor_name", "?")  # N
        F = node.get("func_name", "?")  # F
        S = node.get("stage_mode", "?")  # S
        E = node.get("execution_mode", "?")  # E

        return f"{N}::{F} " f"(S:{S}, E:{E})" f"{visited_note}"

    # 只渲染“子节点”（有父节点）——保证一定画连接符
    def build_child_lines(node: Dict, prefix: str, is_last: bool) -> List[str]:
        connector = "╘-->" if is_last else "╞-->"
        lines = [f"{prefix}{connector}{node_label(node)}"]

        next_stages = node.get("next_stages", []) or []
        # 子节点的 prefix 取决于当前节点是不是 last：last -> 空白，否则竖线延续
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(next_stages):
            lines.extend(
                build_child_lines(child, child_prefix, i == len(next_stages) - 1)
            )
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

    return dict(sorted(clusters.items()))  # 按键排序


# ======== (图论分析) ========
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


# ======== 处理任务 ========
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


# ==== calculate ====
def calc_remaining(processed: int, pending: int, elapsed: float) -> float:
    if processed and pending:
        return pending / processed * elapsed
    return 0


def calc_elapsed(
    status: bool,
    start_time: float,
    last_elapsed: float,
    last_pending: int,
    interval: float,
) -> float:
    """更新时间消耗（仅在 pending 非 0 时刷新）"""
    if status and start_time:
        elapsed = last_elapsed
        # 如果上一次是 pending，则累计时间
        if last_pending:
            # 如果上一次活跃, 那么无论当前状况，累计一次更新时间
            elapsed += interval
    else:
        elapsed = 0

    return elapsed


def calc_global_remain_equal_pred(
    G: nx.DiGraph,
    processed_map: Dict[str, int],
    pending_map: Dict[str, int],
    elapsed_map: Dict[str, float],
) -> Dict[str, float]:
    """
    基于任务图（DAG）估算全局剩余执行时间（偏保守 / 拥塞放大型）。

    本函数仅依赖每个节点的三类观测数据：
    - processed_map: 已完成任务数
    - pending_map:   当前尚未完成的任务数
    - elapsed_map:   已消耗的执行时间（秒）

    核心思想：
    1. 将每个节点当前“已见任务量”定义为：
         seen = processed + pending
    2. 假设下游节点当前已见任务，平均来自其所有上游节点（多上游等贡献假设）。
    3. 使用拓扑序在 DAG 上递推估算每个节点的“预计总输入任务量 total”，
       并据此计算一个放大系数 scale，用于将上游的潜在负载继续传播给下游。
    4. 通过节点的历史平均处理速度（elapsed / processed），
       将“预计剩余任务量”转换为“预计剩余时间”。

    具体计算过程（对每个节点 v）：
    - seen_v = processed_v + pending_v
    - 若 v 无上游节点：
        total_v = seen_v
      否则：
        设 v 有 k 个上游节点，认为 seen_v 平均来自每个上游，
        并按上游的 scale 进行放大：
        total_v = sum( (seen_v / k) * scale[u] )  for u in preds(v)

    - 定义节点的放大系数：
        scale[v] = total_v / max(1, processed_v)

      该定义刻意使用“已完成任务数”作为分母，
      当 processed 很小但 total 很大时，会产生较大的 scale，
      用于显式放大潜在的拥塞与瓶颈风险。

    - 预计剩余任务数：
        remain_tasks_v = max(0, total_v - processed_v)

    - 若节点已处理过任务（processed_v > 0）：
        avg_time = elapsed_v / processed_v
        expected_remain_time[v] = remain_tasks_v * avg_time
      否则：
        expected_remain_time[v] = 0
        （表示尚无法基于历史速度进行时间外推）

    全局剩余时间定义为：
        所有节点 expected_remain_time 的最大值。

    算法特性与设计取向：
    - 假设任务图为有向无环图（DAG），调用方需保证这一前提。
    - 多上游场景下采用“等贡献”假设，不区分不同上游的真实产出比例。
    - 使用 processed 作为放大基准会在系统早期或严重堆积时产生较大的估计值，
      这是有意的设计选择，用于提前暴露潜在的拥塞与失速风险，
      而非提供平滑或乐观的 ETA。
    - 该估算结果偏保守，适合作为监控、告警或瓶颈识别指标。

    :param G             : 任务依赖图（networkx.DiGraph），节点需与 map 的 key 对应
    :param processed_map : 每个节点已完成的任务数量
    :param pending_map   : 每个节点当前剩余的任务数量
    :param elapsed_map   : 每个节点已消耗的执行时间（秒）

    :return: expected_pending_map : 估算得到的全局剩余执行时间（秒）
    """
    expected_pending_map: Dict[str, float] = {}

    # 每个节点的 scale（上游放大系数）
    scale: Dict[str, float] = {}

    for v in nx.topological_sort(G):
        proc_v = float(processed_map.get(v, 0) or 0)
        pend_v = float(pending_map.get(v, 0) or 0)
        elapsed_v = float(elapsed_map.get(v, 0.0) or 0.0)
        seen_v = proc_v + pend_v

        preds = list(G.predecessors(v))
        if not preds:
            # 没上游：就认为总量就是目前看到的量（不外推）
            total_v = seen_v
        else:
            k = float(len(preds))
            obs_each = seen_v / k
            total_v = 0.0
            for u in preds:
                total_v += obs_each * scale.get(u, 1.0)

        scale[v] = total_v / max(1.0, proc_v)  # 下游放大系数
        expect_pend_v = max(0.0, total_v - proc_v)

        # 时间估算：需要 avg time（秒/任务）
        expected_pending_map[v] = calc_remaining(proc_v, expect_pend_v, elapsed_v)

    return expected_pending_map


# ==== other ====

def find_unpickleable(name, obj):
    try:
        pickle.dumps(obj)
        return True
    except Exception as e:
        print("[UNPICKLABLE]", name, type(obj), e)
        return False
