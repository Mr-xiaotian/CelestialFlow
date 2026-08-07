# runtime/util_estimators.py
from __future__ import annotations

from .util_types import StageStatus


def calc_remaining(processed: float, pending: float, elapsed: float) -> float:
    """
    基于已处理任务,剩余任务以及已消耗时间来计算剩余时间.
    不要瞧不起均值,在大规模数据下它可能是最有效的.

    :param processed: 已处理任务数
    :param pending: 待处理任务数
    :param elapsed: 已消耗时间（秒）
    :return: 预计剩余时间（秒）
    """
    if processed and pending:
        return pending / processed * elapsed
    return 0


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


def format_avg_time(elapsed: float, processed: int) -> str:
    """
    格式化平均时间（秒/任务或任务/秒）。

    :param elapsed: 总耗时（秒）
    :param processed: 已处理任务数
    :return: 格式化后的平均时间字符串
    """
    if elapsed and processed:
        avg_time = elapsed / processed
        if avg_time >= 1.0:
            # 显示 "X.XX s/it"
            avg_time_str = f"{avg_time:.2f}s/it"
        else:
            # 显示 "X.XX it/s"（取倒数）
            its_per_sec = processed / elapsed if elapsed else 0
            avg_time_str = f"{its_per_sec:.2f}it/s"
    else:
        avg_time_str = "N/A"

    return avg_time_str
