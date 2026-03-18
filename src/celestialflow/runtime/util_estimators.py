# runtime/util_estimators.py
import networkx as nx


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
    processed_map: dict[str, int],
    pending_map: dict[str, int],
    elapsed_map: dict[str, float],
) -> dict[str, float]:
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
    expected_pending_map: dict[str, float] = {}

    # 每个节点的 scale（上游放大系数）
    scale: dict[str, float] = {}

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
