from __future__ import annotations

import pytest

from celestialflow.runtime.util_estimators import calc_elapsed, calc_remaining
from celestialflow.runtime.util_types import StageStatus


class TestCalcRemaining:
    """calc_remaining — 基于已处理/待处理/已耗时估算剩余时间。"""

    def test_normal_case(self):
        """正常计算：processed=100, pending=50, elapsed=10 -> 5.0。"""
        result = calc_remaining(100, 50, 10)
        assert result == 5.0

    def test_pending_zero_returns_zero(self):
        """pending=0 时剩余时间为 0。"""
        result = calc_remaining(100, 0, 10)
        assert result == 0

    def test_processed_zero_returns_zero(self):
        """processed=0 时无法计算速度，返回 0。"""
        result = calc_remaining(0, 100, 10)
        assert result == 0

    def test_all_zero_returns_zero(self):
        """全部为 0 时返回 0。"""
        result = calc_remaining(0, 0, 0)
        assert result == 0

    def test_float_inputs(self):
        """浮点数输入应保持同样的比例关系。"""
        result = calc_remaining(50.0, 10.0, 3.5)
        assert result == pytest.approx(0.7)

    def test_processed_zero_float(self):
        """processed 为 0.0 时同样返回 0。"""
        result = calc_remaining(0.0, 50.0, 10.0)
        assert result == 0

    def test_pending_zero_float(self):
        """pending 为 0.0 时同样返回 0。"""
        result = calc_remaining(50.0, 0.0, 10.0)
        assert result == 0


class TestCalcElapsed:
    """calc_elapsed — 根据节点状态和上一轮 pending 决定是否累加耗时。"""

    def test_running_with_pending(self):
        """RUNNING 且上一轮 pending>0 时累加 interval。"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=5, interval=2.0
        )
        assert result == 12.0

    def test_running_without_pending(self):
        """RUNNING 且上一轮 pending=0 时保持原值。"""
        result = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=10.0, last_pending=0, interval=2.0
        )
        assert result == 10.0

    def test_stopped_with_pending(self):
        """STOPPED 且上一轮 pending>0 时仍会补记一个 interval。"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=3, interval=5.0
        )
        assert result == 20.0

    def test_stopped_without_pending(self):
        """STOPPED 且上一轮 pending=0 时不再累加。"""
        result = calc_elapsed(
            StageStatus.STOPPED, last_elapsed=15.0, last_pending=0, interval=5.0
        )
        assert result == 15.0

    def test_not_started_returns_zero(self):
        """NOT_STARTED 会直接重置为 0。"""
        result = calc_elapsed(
            StageStatus.NOT_STARTED, last_elapsed=100.0, last_pending=50, interval=10.0
        )
        assert result == 0

    def test_consecutive_calls_simulate_time_progression(self):
        """连续调用时，仅在上一轮有 pending 时累加耗时。"""
        # 第1次：刚启动，还没有 pending 快照 → 不累加
        e1 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=0.0, last_pending=0, interval=1.0
        )
        assert e1 == 0.0

        # 第2次：上一轮有 pending → 累加
        e2 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e1, last_pending=100, interval=1.0
        )
        assert e2 == 1.0

        # 第3次：继续累加
        e3 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e2, last_pending=80, interval=1.0
        )
        assert e3 == 2.0

        # 第4次：pending 变为 0 → 不累加
        e4 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e3, last_pending=0, interval=1.0
        )
        assert e4 == 2.0

    def test_not_started_then_running(self):
        """NOT_STARTED 重置后，切换到 RUNNING 可重新开始累计。"""
        # 状态从 NOT_STARTED 开始
        e1 = calc_elapsed(
            StageStatus.NOT_STARTED, last_elapsed=5.0, last_pending=10, interval=2.0
        )
        assert e1 == 0

        # 切换到 RUNNING
        e2 = calc_elapsed(
            StageStatus.RUNNING, last_elapsed=e1, last_pending=10, interval=2.0
        )
        assert e2 == 2.0
