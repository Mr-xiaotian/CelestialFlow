# runtime/util_estimators.py
from __future__ import annotations

from .util_types import StageStatus


def calc_elapsed(
    status: StageStatus,
    last_elapsed: float,
    last_pending: int,
    interval: float,
) -> float:
    """
    更新时间消耗

    :param status: 节点状态
    :param last_elapsed: 上一次累计的消耗时间（秒）
    :param last_pending: 上一次的待处理任务数
    :param interval: 快照采集间隔（秒）
    :return: 更新后的消耗时间（秒）
    """
    if status in (StageStatus.RUNNING, StageStatus.STOPPED):
        elapsed = last_elapsed
        if last_pending:
            # 如果上一次活跃, 那么无论当前状况，累计一次更新时间
            elapsed += interval
    else:
        elapsed = 0

    return elapsed
