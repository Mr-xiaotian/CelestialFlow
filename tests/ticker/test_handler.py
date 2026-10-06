from __future__ import annotations

import pytest

from celestialflow.runtime.util_errors import ConfigurationError
from celestialflow.ticker import TickEvent, TickHandler


def make_event(seq: int = 1) -> TickEvent:
    """
    构造一个测试用节拍事件。

    :param seq: 节拍序号
    :return: 节拍事件
    """
    return TickEvent(
        seq=seq,
        interval=1.0,
        scheduled_at=float(seq),
        fired_at=float(seq),
        wall_time=float(seq),
        drift=0.0,
        skipped=0,
    )


class BareHandler(TickHandler):
    """不覆写 ``tick_period`` 的最简处理器，用于观察默认值与运行时调整。"""

    def on_tick(self, event: TickEvent) -> None:
        """空实现。

        :param event: 当前节拍事件
        """
        ...


def hit_seqs(handler: TickHandler, upto: int) -> list[int]:
    """
    返回 ``1..upto`` 中会命中该处理器的节拍序号。

    :param handler: 待观察的处理器
    :param upto: 节拍序号上界（含）
    :return: 命中节拍序号列表
    """
    return [
        seq for seq in range(1, upto + 1) if handler.should_tick(make_event(seq))
    ]


def test_handler_default_tick_period_is_one() -> None:
    """未声明 ``tick_period`` 的处理器默认每拍都触发。"""
    handler = BareHandler()

    assert handler.tick_period == 1
    assert hit_seqs(handler, 5) == [1, 2, 3, 4, 5]


def test_set_tick_period_takes_effect_on_should_tick() -> None:
    """``set_tick_period`` 应更新取值并即刻影响 ``should_tick`` 的过滤。"""
    handler = BareHandler()
    handler.set_tick_period(2)
    assert handler.tick_period == 2
    assert hit_seqs(handler, 7) == [1, 3, 5, 7]

    # 相位重新锚定到 seq == 1。
    handler.set_tick_period(3)
    assert hit_seqs(handler, 7) == [1, 4, 7]


def test_set_tick_period_rejects_non_positive() -> None:
    """非正的 ``tick_period`` 应被拒绝，且不改变原取值。"""
    handler = BareHandler()
    handler.set_tick_period(3)

    with pytest.raises(ConfigurationError):
        handler.set_tick_period(0)

    assert handler.tick_period == 3
