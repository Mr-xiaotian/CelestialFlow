# graph/util_serialize.py
from __future__ import annotations

from typing import Any


# ==== 图结构处理 ====
def format_structure_list_from_graph(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]:
    """
    从标准化图结构生成格式化任务结构文本列表（带边框）。

    :param structure: ``nodes + edges + source_nodes`` 形式的图结构
    :return: 带边框的格式化字符串列表
    """
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
        F = node.get("func_name", "?")  # 函数名
        E = node.get("execution_mode", "?")  # 执行模式
        W = node.get("max_workers", "?")  # 最大工作数

        return f"{node_name}::{F} (E:{E}, W:{W}){visited_note}"

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

        # 子节点缩进取决于当前节点是否为最后一个：最后一个留空，否则延续竖线
        child_prefix = prefix + ("    " if is_last else "│   ")
        next_stages = edges.get(node_name, []) or []
        for i, child_name in enumerate(next_stages):
            lines.extend(
                build_child_lines(child_name, child_prefix, i == len(next_stages) - 1)
            )
        return lines

    # 根节点不画连接符，也不继承祖先竖线
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
