from __future__ import annotations

import sqlite3
from queue import Empty

import pytest

from celestialflow.persistence import (
    funnel_scope,
    get_lifecycle_inlet,
    get_lifecycle_spout,
    get_log_inlet,
    get_log_spout,
)
from tests.conftest import wait_until


@pytest.fixture(autouse=True)
def _cleanup_global_spouts() -> None:
    """为每个用例清理全局 spout，避免后台线程与文件状态串扰。"""
    _reset_spout(get_log_spout())
    _reset_spout(get_lifecycle_spout())
    yield
    _reset_spout(get_log_spout())
    _reset_spout(get_lifecycle_spout())


def _reset_spout(spout) -> None:
    """停止并清空全局 spout，避免历史队列记录污染当前用例。"""
    spout.stop()
    while True:
        try:
            _ = spout.get_queue().get_nowait()
        except Empty:
            break

    counter = spout.get_counter()
    while counter.get_count() > 0:
        counter.decrement()


class TestFunnelScope:
    def test_funnel_scope_starts_and_stops_global_spouts(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`funnel_scope()` 应自动管理全局 log/lifecycle spout 生命周期。"""
        monkeypatch.chdir(tmp_path)

        with funnel_scope():
            log_spout = get_log_spout()
            lifecycle_spout = get_lifecycle_spout()

            assert log_spout._thread is not None
            assert lifecycle_spout._thread is not None
            assert log_spout._thread.is_alive()
            assert lifecycle_spout._thread.is_alive()

            get_log_inlet().start_graph("scope_graph", "thread", ["hello scope"])
            get_lifecycle_inlet().task_in("scope_stage", event_id=1, task="data")
            get_lifecycle_inlet().task_success(event_id=1, result="ok")

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

        log_path = get_log_spout().log_path
        lifecycle_path = get_lifecycle_spout().db_path

        assert log_path is not None
        assert lifecycle_path is not None
        assert log_path.exists()
        assert lifecycle_path.exists()
        assert "hello scope" in log_path.read_text(encoding="utf-8")

        conn = sqlite3.connect(lifecycle_path)
        try:
            rows = conn.execute(
                """
                SELECT stage, status, task_json, result_json
                FROM records
                ORDER BY id ASC
                """
            ).fetchall()
        finally:
            conn.close()

        assert rows == [("scope_stage", "success", '"data"', '"ok"')]

    def test_funnel_scope_is_reusable(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`funnel_scope()` 应支持多次独立进入与退出。"""
        monkeypatch.chdir(tmp_path)

        with funnel_scope():
            first_log_thread = get_log_spout()._thread
            first_lifecycle_thread = get_lifecycle_spout()._thread

            assert first_log_thread is not None
            assert first_lifecycle_thread is not None
            assert first_log_thread.is_alive()
            assert first_lifecycle_thread.is_alive()

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

        with funnel_scope():
            second_log_thread = get_log_spout()._thread
            second_lifecycle_thread = get_lifecycle_spout()._thread

            assert second_log_thread is not None
            assert second_lifecycle_thread is not None
            assert second_log_thread.is_alive()
            assert second_lifecycle_thread.is_alive()

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

    def test_funnel_scope_wraps_body_error_and_stops_spouts(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """作用域内部抛异常时，`funnel_scope()` 仍应执行收尾。"""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(
            ExceptionGroup, match="Errors occurred during funnel scope"
        ), funnel_scope():
            get_log_inlet().start_graph("scope_graph", "thread", ["body failure"])
            wait_until(
                lambda: get_log_spout().log_path is not None,
                message="timeout waiting for log scope to initialize",
            )
            raise RuntimeError("body boom")

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None

    def test_funnel_scope_does_not_claim_nested_reuse(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """当前 `funnel_scope()` 为单层作用域，不验证嵌套复用语义。"""
        monkeypatch.chdir(tmp_path)

        with funnel_scope():
            get_log_inlet().start_graph("scope_graph", "thread", ["single layer"])
            wait_until(
                lambda: get_log_spout().log_path is not None,
                message="timeout waiting for log scope to initialize",
            )

        assert get_log_spout()._thread is None
        assert get_lifecycle_spout()._thread is None
