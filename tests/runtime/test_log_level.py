import pytest

from celestialflow.runtime.util_errors import ConfigurationError, InvalidOptionError
from celestialflow.runtime.util_log_level import normalize_log_level


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
