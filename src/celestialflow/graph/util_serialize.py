# graph/util_serialize.py
from __future__ import annotations

from typing import Any

from ..stage.util_types import AnyTaskStage


# ======== 处理图结构 ========
def build_structure_graph(
    stage_dict: dict[str, AnyTaskStage],
    out_edges: dict[str, list[str]],
    source_stages: list[AnyTaskStage],
) -> dict[str, Any]:
    """
    从源节点、邻接表和节点字典构建标准化图结构。

    返回的结构采用 ``nodes + edges + source_nodes`` 形式：
    - ``nodes``: 以节点名为 key 的节点元信息字典
    - ``edges``: 邻接表 {stage_name: [next_stage_name, ...]}
    - ``source_nodes``: 图入口节点名称列表

    :param stage_dict: {stage_name: AnyTaskStage}
    :param out_edges: 邻接表 {stage_name: [next_stage_name, ...]}
    :param source_stages: 源节点列表
    :return: 标准化图结构字典
    """
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[str, list[str]] = {}

    for stage_name, stage in stage_dict.items():
        node_summary = dict(stage.get_summary())
        node_summary.pop("name", None)
        nodes[stage_name] = node_summary
        edges[stage_name] = list(out_edges.get(stage_name, []))

    return {
        "nodes": nodes,
        "edges": edges,
        "source_nodes": [stage.get_name() for stage in source_stages],
    }


def format_structure_list_from_graph(
    structure: dict[str, Any] | None = None,
) -> list[str]:
    """
    从标准化图结构生成格式化任务结构文本列表（带边框）。

    :param structure: ``nodes + edges + source_nodes`` 形式的图结构
    :return: 带边框的格式化字符串列表
    """

    nodes: dict[str, dict[str, Any]] = dict((structure or {}).get("nodes", {}) or {})
    edges: dict[str, list[str]] = dict((structure or {}).get("edges", {}) or {})
    source_nodes: list[str] = list((structure or {}).get("source_nodes", []) or [])

    if not nodes:
        return ["+ No stages defined +"]

    if not source_nodes:
        child_names = {child for child_list in edges.values() for child in child_list}
        source_nodes = [name for name in nodes if name not in child_names]
    if not source_nodes:
        source_nodes = [next(iter(nodes))]

    expanded_nodes: set[str] = set()

    def node_label(node_name: str, *, is_ref: bool = False) -> str:
        """
        生成节点的显示标签字符串。

        :param node_name: 节点名称
        :param is_ref: 是否按引用节点展示
        :return: 格式化的标签字符串
        """
        node = nodes.get(node_name, {})
        visited_note = " [Ref]" if is_ref else ""
        F = node.get("func_name", "?")  # F
        S = node.get("stage_mode", "?")  # S
        E = node.get("execution_mode", "?")  # E
        W = node.get("max_workers", "?")  # W

        return f"{node_name}::{F} (S:{S}, E:{E}, W:{W}){visited_note}"

    # 只渲染"子节点"（有父节点）——保证一定画连接符
    def build_child_lines(node_name: str, prefix: str, is_last: bool) -> list[str]:
        """
        递归构建子节点的树形显示行。

        :param node_name: 子节点名称
        :param prefix: 当前行的缩进前缀
        :param is_last: 是否为同级最后一个节点
        :return: 格式化的行列表
        """
        connector = "╘-->" if is_last else "╞-->"
        is_ref = node_name in expanded_nodes
        lines = [f"{prefix}{connector}{node_label(node_name, is_ref=is_ref)}"]
        if is_ref:
            return lines

        expanded_nodes.add(node_name)

        # 子节点的 prefix 取决于当前节点是不是 last：last -> 空白，否则竖线延续
        child_prefix = prefix + ("    " if is_last else "│   ")
        next_stages = edges.get(node_name, []) or []
        for i, child_name in enumerate(next_stages):
            lines.extend(
                build_child_lines(child_name, child_prefix, i == len(next_stages) - 1)
            )
        return lines

    # 专门处理 root：不画连接符，不产生祖先竖线
    def build_root_lines(root_name: str) -> list[str]:
        """
        构建根节点及其子树的树形显示行。

        :param root_name: 根节点名称
        :return: 格式化的行列表
        """
        is_ref = root_name in expanded_nodes
        lines = [node_label(root_name, is_ref=is_ref)]
        if is_ref:
            return lines

        expanded_nodes.add(root_name)
        next_stages = edges.get(root_name, []) or []
        for i, child_name in enumerate(next_stages):
            lines.extend(build_child_lines(child_name, "", i == len(next_stages) - 1))
        return lines

    all_lines: list[str] = []
    rendered_roots: list[str] = []
    for root_name in source_nodes:
        if all_lines:
            all_lines.append("")  # 根之间留空行
        all_lines.extend(build_root_lines(root_name))
        rendered_roots.append(root_name)

    for node_name in nodes:
        if node_name in rendered_roots or node_name in expanded_nodes:
            continue
        if all_lines:
            all_lines.append("")
        all_lines.extend(build_root_lines(node_name))

    max_length = max(len(line) for line in all_lines)
    content_lines = [f"| {line.ljust(max_length)} |" for line in all_lines]
    border = "+" + "-" * (max_length + 2) + "+"
    return [border, *content_lines, border]
