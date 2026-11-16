# ticker/core_event.py
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TickEvent:
    """一次时钟节拍事件。

    描述 :class:`~celestialflow.ticker.core_clock.TickClock` 某次触发时的时序信息。
    除 :attr:`wall_time` 外，所有时间字段均基于 ``time.monotonic()``，不受系统
    墙钟调整影响。

    :param seq: 节拍序号，从 1 开始单调递增
    :param fired_at: 实际触发时刻（monotonic 秒）
    :param wall_time: 实际触发时刻的墙钟时间（``time.time()`` 秒）
    """

    seq: int
    fired_at: float
    wall_time: float
