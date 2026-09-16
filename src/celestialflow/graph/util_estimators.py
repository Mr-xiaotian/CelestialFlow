# graph/util_estimators.py
from __future__ import annotations

from .util_order_graph import OrderGraph, topo_sort


def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
    downstream_map: dict[str, dict[str, int]],
) -> dict[str, int]:
    """
    基于任务图（DAG）估算各节点全局待处理任务数量（偏保守 / 拥塞放大型）。

    对每个上游-下游组合维护独立放大系数 ``scale[u][w]``，表示上游 u 对
    下游 w 的预计输出量：

        scale[u][w] = total_u * output_u->w / max(1, proc_u)

    其中 ``output_u->w / proc_u`` 为 u 对 w 的产出比，取自 u 自身的单次
    快照（与 ``proc_u`` 同源一致），避免跨节点快照时间差的影响。据此递推
    每个节点的预计总输入量：

        total_v = external_v + sum(scale[u][v] for u in preds(v))

    其中 ``external_v = max(0, seen_v - sum(output_u->v))`` 为外部注入任务数，
    不参与上游放大；``seen_v = processed_v + pending_v``。预计剩余任务数为
    ``max(pending_v, total_v - processed_v)``。

    该估算偏保守：上游堆积时对下游显式放大，适合监控、告警与瓶颈识别。

    :param graph          : 任务依赖图，节点需与 map 的 key 对应
    :param processed_map  : 每个节点已完成的任务数量
    :param pending_map    : 每个节点当前剩余的任务数量
    :param downstream_map : 每个节点实际发送给各下游的任务数量，形如
        ``{node: {downstream_name: count}}``，缺失节点或下游按 0 处理

    :return: expected_pending_map : 估算得到的全局待处理任务数量
    """
    expected_pending_map: dict[str, int] = {}

    # 每个节点对各下游的预计输出量：scale[u][w] = total_u * output_u->w / proc_u
    scale: dict[str, dict[str, float]] = {}
    topo_order = topo_sort(graph)
    if topo_order is None:
        raise ValueError("calc_global_pending() requires a DAG OrderGraph")

    for v_str in topo_order:
        proc_v = int(processed_map.get(v_str, 0) or 0)
        pend_v = int(pending_map.get(v_str, 0) or 0)
        seen_v = proc_v + pend_v

        preds = graph.predecessors(v_str)
        if not preds:
            # 没有上游时，总量就等于当前观测到的任务量
            total_v = seen_v
        else:
            # 上游已发送量即为本节点已接收量（共享计数），据此拆分外部注入
            received_sum = sum(
                downstream_map.get(u, {}).get(v_str, 0) for u in preds
            )
            external_v = max(0, seen_v - received_sum)
            # 外部注入不参与上游放大，上游部分累加各上游的预计输出量
            total_v = float(external_v) + sum(scale[u][v_str] for u in preds)

        # v 对各下游 w 的预计输出量：产出比取自 v 自身快照，proc 与 output 同源
        scale[v_str] = {
            w: total_v * downstream_map.get(v_str, {}).get(w, 0) / max(1, proc_v)
            for w in graph.successors(v_str)
        }

        expect_pend_v = max(pend_v, total_v - proc_v)  # 理论上预计值不会小于当前值

        # 这里只输出预计待处理任务量，不做时间维度估算
        expected_pending_map[v_str] = int(expect_pend_v)

    return expected_pending_map