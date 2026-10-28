import pytest

from celestialflow.runtime.core_config import (
    DEFAULT_REPORT_URL,
    ReportConfig,
    normalize_log_level,
)
from celestialflow.runtime.util_errors import ConfigurationError, InvalidOptionError


class TestReportConfig:
    def test_default_url(self) -> None:
        """未指定地址时使用 ``DEFAULT_REPORT_URL``。"""
        assert ReportConfig().url == DEFAULT_REPORT_URL

    def test_strips_whitespace_and_trailing_slash(self) -> None:
        """地址首尾空白与末尾斜杠会被规范化，避免与端点拼接出双斜杠。"""
        assert ReportConfig(url=" http://127.0.0.1:9000/ ").url == (
            "http://127.0.0.1:9000"
        )

    def test_rejects_empty_url(self) -> None:
        """空地址应被拒绝。"""
        with pytest.raises(ConfigurationError):
            ReportConfig(url="   ")

    def test_rejects_non_http_scheme(self) -> None:
        """非 ``http`` / ``https`` 地址应被拒绝。"""
        with pytest.raises(ConfigurationError):
            ReportConfig(url="ftp://127.0.0.1:9000")

    def test_rejects_non_string_url(self) -> None:
        """非字符串地址应被拒绝。"""
        with pytest.raises(ConfigurationError):
            ReportConfig(url=5005)  # type: ignore[arg-type]

    def test_is_frozen(self) -> None:
        """配置对象不可变，避免运行期被意外改写。"""
        with pytest.raises(AttributeError):
            ReportConfig().url = "http://127.0.0.1:9000"  # type: ignore[misc]


class TestNormalizeLogLevel:
    def test_uppercases_and_strips(self) -> None:
        """级别名不区分大小写，并忽略首尾空白。"""
        assert normalize_log_level(" error ") == "ERROR"

    def test_rejects_unknown_level(self) -> None:
        """未知级别应抛出 ``InvalidOptionError``。"""
        with pytest.raises(InvalidOptionError):
            normalize_log_level("VERBOSE")

    def test_rejects_non_string(self) -> None:
        """非字符串级别应抛出 ``ConfigurationError``。"""
        with pytest.raises(ConfigurationError):
            normalize_log_level(30)  # type: ignore[arg-type]
