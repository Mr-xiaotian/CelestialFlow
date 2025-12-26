def format_tree(node: dict, prefix: str = "", is_last: bool = True) -> str:
    """
    将 {"id": x, "children": [...]} 结构格式化为树状文本。

    :param node: 当前节点
    :param prefix: 前缀（递归用）
    :param is_last: 是否是同级最后一个节点
    :return: 树状字符串
    """
    lines = []

    connector = "└── " if is_last else "├── "

    label = str(node["id"])
    if node.get("is_ref"):
        label += " (ref)"

    lines.append(f"{prefix}{connector}{label}")

    children = node.get("children", [])
    if children:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            last = i == len(children) - 1
            lines.append(format_tree(child, next_prefix, last))

    return "\n".join(lines)


def format_tree_root(tree: dict) -> str:
    """
    格式化整棵树（根节点无连接符）
    """
    lines = [str(tree["id"])]

    children = tree.get("children", [])
    for i, child in enumerate(children):
        last = i == len(children) - 1
        lines.append(format_tree(child, "", last))

    return "\n".join(lines)
