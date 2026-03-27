# graph/util_serialize.py
from typing import TYPE_CHECKING, Any, Dict, List, Set

if TYPE_CHECKING:
    from ..stage import TaskStage


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
        N = node.get("name", "?")  # N
        F = node.get("func_name", "?")  # F
        S = node.get("stage_mode", "?")  # S
        E = node.get("execution_mode", "?")  # E

        return f"{N}::{F} (S:{S}, E:{E}){visited_note}"

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
