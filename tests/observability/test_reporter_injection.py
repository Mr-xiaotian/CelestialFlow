from typing import Any

from celestialflow.observability import TaskReporter
from celestialflow.runtime.util_types import TERMINATION_SIGNAL


class FakeResponse:
    """模拟 reporter 拉取注入任务时的 HTTP 响应。"""

    def __init__(self, payload: dict[str, list[Any]]) -> None:
        self.ok = True
        self.status_code = 200
        self._payload = payload

    def json(self) -> dict[str, list[Any]]:
        """返回预设 JSON 载荷。"""
        return self._payload


class FakeSession:
    """模拟 requests.Session，只覆盖 reporter 需要的 get 接口。"""

    def __init__(self, payload: dict[str, list[Any]]) -> None:
        self.payload = payload

    def get(self, *_args: Any, **_kwargs: Any) -> FakeResponse:
        """返回固定注入任务响应。"""
        return FakeResponse(self.payload)


class FakeTaskGraph:
    """记录 put_stage_queue 调用参数。"""

    def __init__(self) -> None:
        self.calls: list[tuple[dict[str, list[Any]], bool]] = []

    def put_stage_queue(
        self, tasks_dict: dict[str, list[Any]], put_termination_signal: bool = True
    ) -> None:
        """保存 reporter 注入到图中的任务字典。"""
        self.calls.append((tasks_dict, put_termination_signal))


class FakeLogInlet:
    """记录 reporter 注入成功/失败日志。"""

    def __init__(self) -> None:
        self.successes: list[tuple[str, list[Any]]] = []
        self.failures: list[tuple[str, list[Any], Exception]] = []
        self.pull_failures: list[Exception] = []

    def inject_tasks_success(self, target_node: str, task_datas: list[Any]) -> None:
        """记录节点注入成功。"""
        self.successes.append((target_node, task_datas))

    def inject_tasks_failed(
        self, target_node: str, task_datas: list[Any], error: Exception
    ) -> None:
        """记录节点注入失败。"""
        self.failures.append((target_node, task_datas, error))

    def pull_tasks_failed(self, error: Exception) -> None:
        """记录拉取失败。"""
        self.pull_failures.append(error)


def test_reporter_accepts_node_to_tasklist_mapping() -> None:
    """Reporter 能消费 {node_name: [tasklist]} 映射并一次性注入整包任务。"""
    graph = FakeTaskGraph()
    log_inlet = FakeLogInlet()
    reporter = TaskReporter("127.0.0.1", 8000, graph, log_inlet)
    reporter._session = FakeSession(
        {
            "StageA": [1, 2, 3],
            "StageB": ["TERMINATION_SIGNAL"],
        }
    )

    reporter._pull_and_inject_tasks()

    assert graph.calls == [
        (
            {
                "StageA": [1, 2, 3],
                "StageB": [TERMINATION_SIGNAL],
            },
            False,
        )
    ]
    assert log_inlet.successes == [
        ("StageA", [1, 2, 3]),
        ("StageB", [TERMINATION_SIGNAL]),
    ]
    assert log_inlet.failures == []
    assert log_inlet.pull_failures == []
