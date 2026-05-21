import pytest

from celestialflow.persistence.core_log import LogInlet, LogSpout


@pytest.fixture
def log_inlet():
    spout = LogSpout()
    spout.start()
    inlet = LogInlet(spout.get_queue(), log_level="ERROR")
    yield inlet
    spout.stop()
