# ticker/core_event.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TickEvent:
    """一次时钟节拍事件。

    描述 :class:`~celestialflow.ticker.core_ticker.Ticker` 某次触发时的时序信息。
    除 :attr:`wall_time` 外，所有时间字段均基于 ``time.monotonic()``，不受系统
    墙钟调整影响。

    :param seq: 节拍序号，从 1 开始单调递增
    :param interval: 本拍使用的基准周期（秒）
    :param scheduled_at: 计划触发时刻（monotonic 秒）
    :param fired_at: 实际触发时刻（monotonic 秒）
    :param wall_time: 实际触发时刻的墙钟时间（``time.time()`` 秒）
    :param drift: 实际触发晚于计划触发的时长（秒），即 ``fired_at - scheduled_at``
    :param skipped: 因上一拍处理超时而被跳过的基准周期数
    """

    seq: int
    interval: float
    scheduled_at: float
    fired_at: float
    wall_time: float
    drift: float
    skipped: int
