import pytest
import time
from pathlib import Path
from celestialflow.persistence.core_fail import FailInlet, FailSpout
from celestialflow.persistence.core_log import LogInlet, LogSpout
from celestialflow.persistence.core_success import SuccessSpout
from celestialflow.runtime.core_envelope import TaskEnvelope

class TestPersistenceIntegration:
    def test_fail_persistence(self, tmp_path, monkeypatch):
        # 切换工作目录以控制 fallback 位置
        monkeypatch.chdir(tmp_path)
        
        spout = FailSpout(error_source="test_source")
        inlet = FailInlet(spout.get_queue())
        
        spout.start()
        try:
            inlet.start_graph([{"node": "s1"}])
            inlet.task_error("s1", err_id=1, error=ValueError("oops"), task="data1")
            inlet.task_error("s1", err_id=2, error=RuntimeError("fail"), task="data2")
            # 给一点时间让后台线程写入文件
            time.sleep(0.2)
        finally:
            spout.stop()
            
        assert spout.total_error_num == 2
        assert spout.jsonl_path.exists()
        
        # 验证读取
        pairs = spout.get_error_pairs()
        assert len(pairs) == 2
        assert pairs[0][0] == "data1"
        assert pairs[0][1].error_type == "ValueError"
        assert pairs[1][0] == "data2"
        assert pairs[1][1].error_type == "RuntimeError"

    def test_log_persistence(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        spout = LogSpout()
        inlet = LogInlet(spout.get_queue(), log_level="INFO")
        
        spout.start()
        try:
            inlet._log("INFO", "test message")
            inlet._log("WARNING", "hello world")
            time.sleep(0.2)
        finally:
            spout.stop()
            
        assert spout.log_path.exists()
        content = spout.log_path.read_text(encoding="utf-8")
        assert "test message" in content
        assert "hello world" in content
        assert "INFO" in content
        assert "WARNING" in content

    def test_success_persistence(self):
        # SuccessSpout 目前只在内存缓存，不写文件
        spout = SuccessSpout()
        
        spout.start()
        try:
            # SuccessSpout 处理的是 TaskEnvelope，且 result 是 envelope.task, task 是 envelope.prev
            env1 = TaskEnvelope(task=100, id=1, source="s1")
            env1.prev = "task1"
            
            env2 = TaskEnvelope(task=200, id=2, source="s2")
            env2.prev = "task2"
            
            spout.get_queue().put(env1)
            spout.get_queue().put(env2)
            time.sleep(0.2)
        finally:
            spout.stop()
            
        pairs = spout.get_success_pairs()
        assert len(pairs) == 2
        assert pairs[0] == ("task1", 100)
        assert pairs[1] == ("task2", 200)
