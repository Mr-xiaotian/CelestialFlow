from celestialflow.runtime.util_config import load_report_url_from_pyproject


def test_load_report_url_reads_url(tmp_path, monkeypatch) -> None:
    """从 ``[tool.celestialflow].url`` 读取上报地址。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nurl = "http://127.0.0.1:9000"\n', encoding="utf-8"
    )

    assert load_report_url_from_pyproject() == "http://127.0.0.1:9000"


def test_load_report_url_returns_none_when_absent(tmp_path, monkeypatch) -> None:
    """未配置 ``url`` 时返回 ``None``。"""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "pyproject.toml").write_text(
        '[tool.celestialflow]\nlog_level = "INFO"\n', encoding="utf-8"
    )

    assert load_report_url_from_pyproject() is None


def test_load_report_url_returns_none_without_pyproject(tmp_path, monkeypatch) -> None:
    """没有 ``pyproject.toml`` 时返回 ``None``。"""
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    monkeypatch.chdir(empty_dir)

    assert load_report_url_from_pyproject() is None
