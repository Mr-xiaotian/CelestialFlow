from __future__ import annotations

import sqlite3

import pytest

from celestialflow.persistence import (
    funnel_scope,
    get_fallback_inlet,
    get_fallback_spout,
    get_log_inlet,
    get_log_spout,
)
from tests.conftest import wait_until


@pytest.fixture(autouse=True)
def _cleanup_global_spouts() -> None:
    """为每个用例清理全局 spout，避免后台线程与文件状态串扰。"""
    get_log_spout().stop()
    get_fallback_spout().stop()
    yield
    get_log_spout().stop()
    get_fallback_spout().stop()


class TestFunnelScope:
    def test_funnel_scope_starts_and_stops_global_spouts(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """`funnel_scope()` 应自动管理全局 log/fallback spout 生命周期。"""
        monkeypatch.chdir(tmp_path)

        with funnel_scope():
            log_spout = get_log_spout()
            fallback_spout = get_fallback_spout()

            assert log_spout._thread is not None
            assert fallback_spout._thread is not None
            assert log_spout._thread.is_alive()
            assert fallback_spout._thread.is_alive()

            get_log_inlet().start_graph("scope_graph", ["hello scope"])
            get_fallback_inlet().task_in("scope_stage", event_id=1, task="data")
            get_fallback_inlet().task_success(event_id=1, result="ok", persist=True)

        assert get_log_spout()._thread is None
        assert get_fallback_spout()._thread is None

        log_path = get_log_spout().log_path
        fallback_path = get_fallback_spout().db_path

        assert log_path is not None
        assert fallback_path is not None
        assert log_path.exists()
        assert fallback_path.exists()
        assert "hello scope" in log_path.read_text(encoding="utf-8")

        conn = sqlite3.connect(fallback_path)
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
            first_fallback_thread = get_fallback_spout()._thread

            assert first_log_thread is not None
            assert first_fallback_thread is not None
            assert first_log_thread.is_alive()
            assert first_fallback_thread.is_alive()

        assert get_log_spout()._thread is None
        assert get_fallback_spout()._thread is None

        with funnel_scope():
            second_log_thread = get_log_spout()._thread
            second_fallback_thread = get_fallback_spout()._thread

            assert second_log_thread is not None
            assert second_fallback_thread is not None
            assert second_log_thread.is_alive()
            assert second_fallback_thread.is_alive()

        assert get_log_spout()._thread is None
        assert get_fallback_spout()._thread is None

    def test_funnel_scope_wraps_body_error_and_stops_spouts(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """作用域内部抛异常时，`funnel_scope()` 仍应执行收尾。"""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(
            ExceptionGroup, match="Errors occurred during funnel scope"
        ), funnel_scope():
            get_log_inlet().start_graph("scope_graph", ["body failure"])
            wait_until(
                lambda: get_log_spout().log_path is not None,
                message="timeout waiting for log scope to initialize",
            )
            raise RuntimeError("body boom")

        assert get_log_spout()._thread is None
        assert get_fallback_spout()._thread is None

    def test_funnel_scope_does_not_claim_nested_reuse(
        self, tmp_path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """当前 `funnel_scope()` 为单层作用域，不验证嵌套复用语义。"""
        monkeypatch.chdir(tmp_path)

        with funnel_scope():
            get_log_inlet().start_graph("scope_graph", ["single layer"])
            wait_until(
                lambda: get_log_spout().log_path is not None,
                message="timeout waiting for log scope to initialize",
            )

        assert get_log_spout()._thread is None
        assert get_fallback_spout()._thread is None
