from __future__ import annotations

import threading
from dataclasses import FrozenInstanceError

from celestialflow.runtime.util_types import (
    CTreeEvent,
    NoOpContext,
    StageStatus,
    SumCounter,
    TerminationIdPool,
    TerminationSignal,
    ValueWrapper,
)


class TestUtilTypes:
    # ---- TerminationSignal ----

    def test_termination_signal_default(self):
        """默认参数构造"""
        sig = TerminationSignal()
        assert sig.id == -1
        assert sig.source == "input"

    def test_termination_signal_custom(self):
        """自定义参数构造"""
        sig = TerminationSignal(_id=42, source="queue")
        assert sig.id == 42
        assert sig.source == "queue"

    def test_termination_signal_partial_kwargs(self):
        """只传部分关键字参数"""
        sig = TerminationSignal(source="scheduler")
        assert sig.id == -1
        assert sig.source == "scheduler"

    # ---- TerminationIdPool ----

    def test_termination_id_pool_non_empty(self):
        """非空列表构造"""
        pool = TerminationIdPool([1, 2, 3])
        assert pool.ids == [1, 2, 3]

    def test_termination_id_pool_empty(self):
        """空列表边界"""
        pool = TerminationIdPool([])
        assert pool.ids == []

    def test_termination_id_pool_single(self):
        """单元素列表"""
        pool = TerminationIdPool([0])
        assert pool.ids == [0]

    # ---- NoOpContext ----

    def test_noop_context_with_statement(self):
        """with 语句正常进出"""
        ctx = NoOpContext()
        with ctx as entered:
            assert entered is ctx
            # 内部代码正常执行
            x = 1 + 1
            assert x == 2
        # 退出后无副作用，变量依然可访问
        assert x == 2

    def test_noop_context_exception_does_not_suppress(self):
        """NoOpContext 不抑制异常"""
        ctx = NoOpContext()
        import pytest

        with pytest.raises(ValueError, match="boom"):
            with ctx:
                raise ValueError("boom")

    def test_noop_context_enter_exit_direct(self):
        """直接调用 __enter__ / __exit__"""
        ctx = NoOpContext()
        assert ctx.__enter__() is ctx
        # __exit__ 返回 None（不抑制异常）
        result = ctx.__exit__(None, None, None)
        assert result is None

    # ---- ValueWrapper ----

    def test_value_wrapper_basic_read_write(self):
        """基本读写"""
        v = ValueWrapper(10)
        assert v.value == 10
        v.value = 20
        assert v.value == 20

    def test_value_wrapper_with_lock(self):
        """带锁的 ValueWrapper 读写行为一致"""
        lock = threading.Lock()
        v = ValueWrapper(5, lock=lock)
        assert v.value == 5
        v.value = 99
        assert v.value == 99

    def test_value_wrapper_with_lock_context_manager(self):
        """带锁时通过 get_lock 进入上下文"""
        lock = threading.Lock()
        v = ValueWrapper(0, lock=lock)
        with v.get_lock():
            v.value += 1
        assert v.value == 1

    def test_value_wrapper_get_lock_returns_lock(self):
        """传入 Lock 时 get_lock 返回 Lock 本身"""
        lock = threading.Lock()
        v = ValueWrapper(0, lock=lock)
        assert v.get_lock() is lock

    def test_value_wrapper_get_lock_returns_noop(self):
        """不传 Lock 时 get_lock 返回 NoOpContext"""
        v = ValueWrapper(0)
        lock = v.get_lock()
        assert isinstance(lock, NoOpContext)

    def test_value_wrapper_negative_value(self):
        """负数值边界"""
        v = ValueWrapper(-100)
        assert v.value == -100

    # ---- SumCounter ----

    def test_sum_counter_single_append(self):
        """单个计数器累加"""
        sc = SumCounter()
        sc.append_counter(ValueWrapper(10))
        sc.append_counter(ValueWrapper(20))
        assert sc.value == 30

    def test_sum_counter_init_value(self):
        """init_value 影响总和"""
        sc = SumCounter()
        sc.add(5)
        assert sc.value == 5
        sc.add(3)
        assert sc.value == 8

    def test_sum_counter_init_and_counters(self):
        """init_value 和 counters 同时累加"""
        sc = SumCounter()
        sc.add(100)
        sc.append_counter(ValueWrapper(50))
        sc.append_counter(ValueWrapper(30))
        assert sc.value == 180

    def test_sum_counter_reset(self):
        """reset 清零所有计数器"""
        sc = SumCounter()
        sc.add(10)
        sc.append_counter(ValueWrapper(20))
        sc.append_counter(ValueWrapper(30))
        assert sc.value == 60

        sc.reset()
        assert sc.value == 0
        assert sc.init_value.value == 0

    def test_sum_counter_reset_partial(self):
        """部分计数器有值，reset 后全部归零"""
        sc = SumCounter()
        sc.append_counter(ValueWrapper(7))
        sc.append_counter(ValueWrapper(0))
        assert sc.value == 7
        sc.reset()
        assert sc.value == 0

    def test_sum_counter_empty(self):
        """无计数器时 value 为 init_value 默认值 0"""
        sc = SumCounter()
        assert sc.value == 0

    def test_sum_counter_multiple_add_init(self):
        """多次 add"""
        sc = SumCounter()
        sc.add(0)
        sc.add(10)
        sc.add(20)
        assert sc.value == 30

    # ---- StageStatus ----

    def test_stage_status_values(self):
        """枚举值正确"""
        assert StageStatus.NOT_STARTED == 0
        assert StageStatus.RUNNING == 1
        assert StageStatus.STOPPED == 2

    def test_stage_status_intenum_behavior(self):
        """IntEnum 可与整数比较"""
        assert isinstance(StageStatus.NOT_STARTED, int)
        assert StageStatus.NOT_STARTED < StageStatus.RUNNING
        assert StageStatus.RUNNING < StageStatus.STOPPED
        assert StageStatus.STOPPED > 1

    def test_stage_status_len(self):
        """枚举成员数量"""
        assert len(StageStatus) == 3

    # ---- CTreeEvent ----

    def test_ctree_event_task_values(self):
        """任务相关常量"""
        assert CTreeEvent.TASK_INPUT == "task.input"
        assert CTreeEvent.TASK_SUCCESS == "task.success"
        assert CTreeEvent.TASK_ERROR == "task.error"
        assert CTreeEvent.TASK_RETRY_PREFIX == "task.retry."
        assert CTreeEvent.TASK_DUPLICATE == "task.duplicate"

    def test_ctree_event_termination_values(self):
        """终止相关常量"""
        assert CTreeEvent.TERMINATION_INPUT == "termination.input"
        assert CTreeEvent.TERMINATION_MERGE == "termination.merge"

    def test_ctree_event_retry_prefix_ends_with_dot(self):
        """重试前缀以点结尾"""
        assert CTreeEvent.TASK_RETRY_PREFIX.endswith(".")


# 运行方式：
#   python -m pytest tests/utils/test_utils_types.py -v
