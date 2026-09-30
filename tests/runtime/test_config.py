import pytest

from celestialflow.runtime.util_config import (
    DEFAULT_REPORT_URL,
    load_if_report_from_pyproject,
    load_report_url_from_pyproject,
)
from celestialflow.runtime.util_errors import ConfigurationError


def test_load_report_url_reads_report_url(tmp_path, monkeypatch) -> None:
    """从 ``[tool.celestialflow].report_url`` 读取上报地址。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nreport_url = "http://127.0.0.1:9000"\n',
        encoding="utf-8",
    )

    assert load_report_url_from_pyproject() == "http://127.0.0.1:9000"


def test_load_report_url_defaults_when_absent(tmp_path, monkeypatch) -> None:
    """未配置 ``report_url`` 时返回默认地址。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nlog_level = "INFO"\n', encoding="utf-8"
    )

    assert load_report_url_from_pyproject() == DEFAULT_REPORT_URL


def test_load_report_url_defaults_without_pyproject(tmp_path, monkeypatch) -> None:
    """没有 ``pyproject.toml`` 时返回默认地址。"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)

    assert load_report_url_from_pyproject() == DEFAULT_REPORT_URL


def test_load_if_report_reads_true(tmp_path, monkeypatch) -> None:
    """从 ``[tool.celestialflow].if_report`` 读取上报开关。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        "[tool.celestialflow]\nif_report = true\n", encoding="utf-8"
    )

    assert load_if_report_from_pyproject() is True


def test_load_if_report_defaults_to_false(tmp_path, monkeypatch) -> None:
    """未配置 ``if_report`` 时返回 ``False``。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nreport_url = "http://127.0.0.1:9000"\n',
        encoding="utf-8",
    )

    assert load_if_report_from_pyproject() is False


def test_load_if_report_returns_false_without_pyproject(tmp_path, monkeypatch) -> None:
    """没有 ``pyproject.toml`` 时返回 ``False``。"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)

    assert load_if_report_from_pyproject() is False


def test_load_if_report_rejects_non_boolean(tmp_path, monkeypatch) -> None:
    """``if_report`` 非布尔时抛出 ``ConfigurationError``。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nif_report = "yes"\n', encoding="utf-8"
    )

    with pytest.raises(ConfigurationError):
        load_if_report_from_pyproject()
