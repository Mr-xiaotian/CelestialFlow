from typing import Any, Dict
from datetime import datetime, timezone

def format_unix_nano(ts: int) -> str:
    """
    将 Unix 纳秒时间戳转换为可读时间（UTC）
    例：2026-01-13 10:42:31.123456
    """
    sec = ts // 1_000_000_000
    ns = ts % 1_000_000_000
    dt = datetime.fromtimestamp(sec, tz=timezone.utc)
    # 保留微秒精度（ns -> us）
    return dt.strftime("%Y-%m-%d %H:%M:%S") + f".{ns // 1000:06d} UTC"


def _node_label(node: Dict[str, Any]) -> str:
    # 必须字段：id
    label = str(node["id"])

    # ref 标记
    if node.get("is_ref"):
        label += " [Ref]"

    # 可选 meta：type / time_unix_nano
    ntype = node.get("type")
    if ntype:
        label += f" ({ntype})"

    ts = node.get("time_unix_nano")
    if ts is not None:
        # 你也可以在这里把 ns 转成人类可读时间；我先保持原样，避免时区/格式争议
        label += f" @{format_unix_nano(ts)}"

    return label


def format_descendants(node: Dict[str, Any], prefix: str = "", is_last: bool = True) -> str:
    """
    将树结构格式化为树状文本。
    兼容:
      - struct view: {"id": x, "children": [...], "is_ref": bool?}
      - meta view:   {"id": x, "type": "...", "time_unix_nano": 123, "children": [...], "is_ref": bool?}
    """
    lines = []
    connector = "╘-->" if is_last else "╞-->"

    lines.append(f"{prefix}{connector}{_node_label(node)}")

    children = node.get("children") or []
    if children:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(children):
            lines.append(format_descendants(child, next_prefix, i == len(children) - 1))

    return "\n".join(lines)


def format_descendants_root(tree: Dict[str, Any]) -> str:
    """
    格式化整棵树（根节点无连接符）
    """
    lines = [_node_label(tree)]

    children = tree.get("children") or []
    for i, child in enumerate(children):
        lines.append(format_descendants(child, "", i == len(children) - 1))

    return "\n".join(lines)


def format_provenance(
    node: Dict[str, Any],
    prefix: str = "",
    is_last: bool = True,
) -> str:
    """
    将 provenance 树（parents 方向）格式化为树状文本。

    兼容:
      - struct view: {"id": x, "parents": [...], "is_ref": bool?}
      - meta view:   {"id": x, "type": "...", "time_unix_nano": 123,
                      "parents": [...], "is_ref": bool?}
    """
    lines = []
    connector = "╘<--" if is_last else "╞<--"

    lines.append(f"{prefix}{connector}{_node_label(node)}")

    parents = node.get("parents") or []
    if parents:
        next_prefix = prefix + ("    " if is_last else "│   ")
        for i, parent in enumerate(parents):
            lines.append(
                format_provenance(
                    parent,
                    next_prefix,
                    i == len(parents) - 1,
                )
            )

    return "\n".join(lines)


def format_provenance_root(tree: Dict[str, Any]) -> str:
    """
    格式化整棵 provenance 树（根节点无连接符）
    """
    lines = [_node_label(tree)]

    parents = tree.get("parents") or []
    for i, parent in enumerate(parents):
        lines.append(
            format_provenance(
                parent,
                "",
                i == len(parents) - 1,
            )
        )

    return "\n".join(lines)
