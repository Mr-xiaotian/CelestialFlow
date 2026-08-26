# graph/util_estimators.py
from __future__ import annotations

from .util_order_graph import OrderGraph, topo_sort


def calc_global_pending(
    graph: OrderGraph,
    processed_map: dict[str, int],
    pending_map: dict[str, int],
) -> dict[str, int]:
    """
    基于任务图（DAG）估算全局待处理任务数量（偏保守 / 拥塞放大型）。

    本函数仅依赖每个节点的两类观测数据：
    - processed_map: 已完成任务数
    - pending_map:   当前尚未完成的任务数

    核心思想：
    1. 将每个节点当前"已见任务量"定义为：
         seen = processed + pending
    2. 假设下游节点当前已见任务，平均来自其所有上游节点（多上游等贡献假设）。
    3. 使用拓扑序在 DAG 上递推估算每个节点的"预计总输入任务量 total"，
       并据此计算一个放大系数 scale，用于将上游的潜在负载继续传播给下游。
    4. 通过节点的历史平均处理速度（elapsed / processed），
       将"预计剩余任务量"转换为"预计剩余时间"。

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

      该定义刻意使用"已完成任务数"作为分母，
      当 processed 很小但 total 很大时，会产生较大的 scale，
      用于显式放大潜在的拥塞与瓶颈风险。

    - 预计剩余任务数：
        expect_pend_v = max(pend_v, total_v - proc_v)
        即至少保留当前观测到的 pending，同时按上游放大后的总量外推。

    本实现仅输出各节点预计剩余任务数（任务量），不进行时间维度的外推。

    算法特性与设计取向：
    - 假设任务图为有向无环图（DAG），调用方需保证这一前提。
    - 多上游场景下采用"等贡献"假设，不区分不同上游的真实产出比例。
    - 使用 processed 作为放大基准会在系统早期或严重堆积时产生较大的估计值，
      这是有意的设计选择，用于提前暴露潜在的拥塞与失速风险，
      而非提供平滑或乐观的 ETA。
    - 该估算结果偏保守，适合作为监控、告警或瓶颈识别指标。

    :param graph         : 任务依赖图，节点需与 map 的 key 对应
    :param processed_map : 每个节点已完成的任务数量
    :param pending_map   : 每个节点当前剩余的任务数量

    :return: expected_pending_map : 估算得到的全局待处理任务数量
    """
    expected_pending_map: dict[str, int] = {}

    # 每个节点的放大系数（用于传播上游负载）
    scale: dict[str, float] = {}
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
            k = float(len(preds))
            obs_each = seen_v / k
            total_v = 0
            for u in preds:
                total_v += obs_each * scale.get(u, 1.0)

        scale[v_str] = total_v / max(1, proc_v)  # 当前节点的放大系数
        expect_pend_v = max(pend_v, total_v - proc_v)  # 理论上预计值不会小于当前值

        # 这里只输出预计待处理任务量，不做时间维度估算
        expected_pending_map[v_str] = int(expect_pend_v)

    return expected_pending_map
