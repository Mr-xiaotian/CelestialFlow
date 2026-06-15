from celestialflow.persistence.core_success import SuccessSpout
from celestialflow.runtime.core_envelope import TaskEnvelope
from tests.conftest import wait_until


class TestSuccessPersistence:
    def test_success_persistence(self):
        """`SuccessSpout` 应缓存 `TaskEnvelope` 中的 task-result 对。"""
        spout = SuccessSpout()

        spout.start()
        try:
            env1 = TaskEnvelope(task=100, id=1)
            env1.prev = 'task1'

            env2 = TaskEnvelope(task=200, id=2)
            env2.prev = 'task2'

            spout.get_queue().put(env1)
            spout.get_queue().put(env2)
            wait_until(
                lambda: len(spout.get_success_pairs()) == 2,
                message='timeout waiting for success_spout to process records',
            )
        finally:
            spout.stop()

        pairs = spout.get_success_pairs()
        assert len(pairs) == 2
        assert pairs[0] == ('task1', 100)
        assert pairs[1] == ('task2', 200)
