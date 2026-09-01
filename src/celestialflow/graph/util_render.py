# graph/util_render.py
from __future__ import annotations


# ==== 图结构处理 ====
def render_structure_list(
    nodes: list[str],
    edges: dict[str, list[str]],
    source_nodes: list[str],
) -> list[str]:
    """
    从图结构（节点元信息、邻接表、源节点）生成带边框的树形文本列表。

    渲染规则：
    - 以 ``source_nodes`` 为根，按 ``edges`` 邻接表展开为树形文本；
    - 环或共享子图节点只展开一次，再次出现时标记 ``[Ref]``；
    - 未从任意根渲染到的节点（孤立节点）追加在末尾；
    - 根节点不画连接符，子节点使用 ``╞-->`` / ``╘-->`` 连接符。

    :param nodes: 节点名称列表
    :param edges: 邻接表 {stage_name: [next_stage_name, ...]}
    :param source_nodes: 源节点名称列表
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
        visited_note = " [Ref]" if is_ref else ""
        return f"{node_name}{visited_note}"

    # 显式栈迭代的 DFS 先序遍历，避免深链图触发 Python 递归上限（默认约 1000 层）。
    # 栈帧: (node_name, prefix, is_last, is_root)。is_root 表示根节点：
    # 根节点不画连接符且其子节点前缀为空；其余节点前缀由父节点的 is_last 决定。
    lines: list[str] = []
    stack: list[tuple[str, str, bool, bool]] = []

    def visit(node_name: str, prefix: str, is_last: bool, is_root: bool) -> None:
        """
        输出节点行，并将未展开子节点按逆序压入栈（保证弹栈顺序为 DFS 先序）。

        :param node_name: 节点名称
        :param prefix: 当前行的缩进前缀
        :param is_last: 是否为同级最后一个节点
        :param is_root: 是否为根节点（不画连接符，子节点前缀为空）
        :return: ``None``
        """
        if is_root:
            lines.append(node_label(node_name, is_ref=node_name in expanded_nodes))
        else:
            connector = "╘-->" if is_last else "╞-->"
            lines.append(
                f"{prefix}{connector}"
                f"{node_label(node_name, is_ref=node_name in expanded_nodes)}"
            )
        if node_name in expanded_nodes:
            return

        expanded_nodes.add(node_name)

        # 子节点缩进取决于当前节点是否为最后一个：最后一个留空，否则延续竖线
        child_prefix = "" if is_root else prefix + ("    " if is_last else "│   ")
        next_stages = edges.get(node_name, [])
        for i in range(len(next_stages) - 1, -1, -1):
            stack.append(
                (next_stages[i], child_prefix, i == len(next_stages) - 1, False)
            )

    rendered_roots: list[str] = []
    for root_name in source_nodes:
        if lines:
            lines.append("")  # 根之间留空行
        stack.append((root_name, "", False, True))
        while stack:
            node_name, prefix, is_last, is_root = stack.pop()
            visit(node_name, prefix, is_last, is_root)
        rendered_roots.append(root_name)

    for node_name in nodes:
        if node_name in rendered_roots or node_name in expanded_nodes:
            continue
        if lines:
            lines.append("")
        stack.append((node_name, "", False, True))
        while stack:
            node_name, prefix, is_last, is_root = stack.pop()
            visit(node_name, prefix, is_last, is_root)

    max_length = max(len(line) for line in lines)
    content_lines = [f"| {line.ljust(max_length)} |" for line in lines]
    border = "+" + "-" * (max_length + 2) + "+"
    return [border, *content_lines, border]
