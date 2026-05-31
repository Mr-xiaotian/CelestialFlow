from __future__ import annotations

import time
from collections.abc import Callable

import pytest
from dotenv import load_dotenv

load_dotenv()


def wait_until(
    condition: Callable[[], bool],
    *,
    timeout: float = 5.0,
    interval: float = 0.05,
    message: str = "condition was not satisfied in time",
) -> None:
    """轮询等待条件成立，统一测试中的后台线程同步写法。"""
    deadline = time.perf_counter() + timeout
    while time.perf_counter() < deadline:
        if condition():
            return
        time.sleep(interval)

    if condition():
        return

    pytest.fail(message)


def assert_stays_true(
    condition: Callable[[], bool],
    *,
    duration: float = 0.3,
    interval: float = 0.05,
    message: str = "condition changed unexpectedly",
) -> None:
    """在一小段时间内持续验证条件保持为真。"""
    deadline = time.perf_counter() + duration
    while time.perf_counter() < deadline:
        if not condition():
            pytest.fail(message)
        time.sleep(interval)
