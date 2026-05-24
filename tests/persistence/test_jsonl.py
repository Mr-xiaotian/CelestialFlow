import json
import pytest
from celestialflow.persistence.util_jsonl import (
    load_jsonl_logs,
    load_jsonl_by_key,
    load_jsonl_grouped_by_keys,
    load_task_error_pairs,
    parse_jsonl_value,
)

@pytest.fixture
def sample_jsonl(tmp_path):
    path = tmp_path / "test.jsonl"
    data = [
        {"meta": "header"},
        {"stage": "s1", "task": "1", "error": "ValueError(err1)", "error_type": "ValueError", "error_message": "err1"},
        {"stage": "s1", "task": "2", "error": "TypeError(err2)", "error_type": "TypeError", "error_message": "err2"},
        {"stage": "s2", "task": "3", "error": "ValueError(err1)", "error_type": "ValueError", "error_message": "err1"},
        {"stage": "s1", "task": "(1, 2)", "error": "ValueError(err1)"}
    ]
    with open(path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    return path

class TestJsonlUtils:
    def test_parse_jsonl_value(self):
        """测试 JSONL 值的智能解析逻辑：支持数字、布尔值及序列化后的容器"""
        assert parse_jsonl_value("1") == 1
        assert parse_jsonl_value("True") is True
        assert parse_jsonl_value("[1, 2]") == (1, 2)
        assert parse_jsonl_value("(1, 2)") == (1, 2)
        assert parse_jsonl_value("just a string") == "just a string"

    def test_load_jsonl_logs(self, sample_jsonl):
        """测试从 JSONL 文件中批量加载日志行，支持按起始序号和字段过滤"""
        logs = load_jsonl_logs(str(sample_jsonl), start_seq=1)
        assert len(logs) == 4
        assert logs[0]["stage"] == "s1"

        # 测试 key 过滤
        logs_filtered = load_jsonl_logs(str(sample_jsonl), start_seq=1, keys=["stage"])
        assert len(logs_filtered) == 4
        assert set(logs_filtered[0].keys()) == {"stage"}

    def test_load_jsonl_by_key(self, sample_jsonl):
        """测试按指定键（如 stage）对 JSONL 数据进行分组提取"""
        # 默认按 stage 分组提取 task
        grouped = load_jsonl_by_key(sample_jsonl)
        assert "s1" in grouped
        assert "s2" in grouped
        assert grouped["s1"] == [1, 2, (1, 2)]
        assert grouped["s2"] == [3]

    def test_load_jsonl_grouped_by_keys(self, sample_jsonl):
        """测试按多个键的组合对 JSONL 数据进行分组提取"""
        # 按 error 和 stage 组合分组
        grouped = load_jsonl_grouped_by_keys(
            sample_jsonl,
            group_keys=["error", "stage"],
            extract_field="task"
        )
        assert ("ValueError(err1)", "s1") in grouped
        assert ("ValueError(err1)", "s2") in grouped
        assert grouped[("ValueError(err1)", "s1")] == [1, (1, 2)]

    def test_load_task_error_pairs(self, sample_jsonl):
        """测试加载任务-错误对，并验证其结构化解析为 PersistedErrorRecord"""
        pairs = load_task_error_pairs(sample_jsonl)
        # 第一行 meta 会被跳过（因为没有 task/error 键）
        assert len(pairs) == 4
        task, error = pairs[0]
        assert task == 1
        assert error.error_type == "ValueError"
        assert error.error_message == "err1"
        assert error.stage == "s1"
