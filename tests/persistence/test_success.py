from celestialflow.persistence.core_fallback import FallbackInlet, FallbackSpout


class TestSuccessPersistence:
    def test_success_persistence(self, tmp_path, monkeypatch):
        """`FallbackSpout` 应持久化 success 结果并可读回 task-result 对。"""
        monkeypatch.chdir(tmp_path)
        spout = FallbackSpout(error_source="success_source")
        inlet = FallbackInlet(spout.get_queue())

        spout.start()
        try:
            inlet.task_in("s1", event_id=1, task="task1")
            inlet.task_success(event_id=1, result=100, cache=True)
            inlet.task_in("s2", event_id=2, task="task2")
            inlet.task_success(event_id=2, result=200, cache=True)
        finally:
            spout.stop()

        pairs = spout.get_task_result_pairs()
        assert len(pairs) == 2
        assert pairs[0] == ("task1", 100)
        assert pairs[1] == ("task2", 200)
