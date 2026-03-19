# observability/core_report.py
from threading import Event, Thread
from typing import TYPE_CHECKING

import requests

from ..persistence import LogSinker
from ..persistence.util_jsonl import load_jsonl_logs
from ..runtime.util_types import TERMINATION_SIGNAL

if TYPE_CHECKING:
    from ..graph import TaskGraph


class TaskReporter:
    """
    周期性向远程服务推送任务运行状态的上报器。

    - 定时从服务器拉取配置（如上报间隔、任务注入信息）
    - 将任务图中的状态、错误、结构、拓扑等信息推送到后端接口
    - 以后台线程方式运行，可随时 start()/stop()
    - 主要用于可视化监控、任务远程控制与 Web UI 同步
    """

    def __init__(
        self,
        host: str,
        port: int,
        task_graph: "TaskGraph",
        log_sinker: LogSinker,
    ) -> None:
        """
        初始化任务上报器
        
        :param host: 远程服务主机地址
        :param port: 远程服务端口
        :param task_graph: 任务图实例
        :param log_sinker: 日志下沉器实例
        """
        self.base_url = f"http://{host}:{port}"
        self.task_graph = task_graph
        self.log_sinker = log_sinker

        self._stop_flag = Event()
        self._thread = None
        self._push_errors_mode = "meta"

        self.interval = 5
        self.history_limit = 20

    def start(self) -> None:
        """启动上报器线程"""
        if self._thread is None or not self._thread.is_alive():
            self._stop_flag.clear()
            self._thread = Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """停止上报器线程"""
        if self._thread:
            self._refresh_all()  # 最后一次
            self._stop_flag.set()
            self._thread.join(timeout=2)
            self._thread = None
            self.log_sinker.stop_reporter()

    def _pull_timeout(self) -> float:
        """计算拉取请求的超时时间"""
        return max(1.0, min(self.interval * 0.2, 5.0))

    def _push_timeout(self) -> float:
        """计算推送请求的超时时间"""
        return max(1.0, min(self.interval * 0.2, 3.0))

    def _loop(self) -> None:
        """上报器主循环"""
        while not self._stop_flag.is_set():
            try:
                self._refresh_all()
            except Exception as e:
                self.log_sinker.loop_failed(e)
            self._stop_flag.wait(self.interval)

    def _refresh_all(self) -> None:
        """刷新所有上报内容"""
        # 拉取逻辑
        self._pull_interval()
        self._pull_history_limit()
        self._pull_and_inject_tasks()

        # 推送逻辑
        self._push_errors()
        self._push_status()
        self._push_structure()
        self._push_topology()
        self._push_summary()
        self._push_history()

    def _pull_interval(self) -> None:
        """从远程服务拉取上报间隔配置"""
        try:
            res = requests.get(
                f"{self.base_url}/api/pull_interval", timeout=self._pull_timeout()
            )
            if res.ok:
                interval = res.json().get("interval", 5)
                self.interval = max(1.0, min(interval, 60.0))
        except Exception as e:
            self.log_sinker.pull_interval_failed(e)

    def _pull_history_limit(self) -> None:
        """从远程服务拉取历史记录限制配置"""
        try:
            res = requests.get(
                f"{self.base_url}/api/pull_history_limit", timeout=self._pull_timeout()
            )
            if res.ok:
                history_limit = res.json().get("historyLimit", 20)
                self.history_limit = max(1, min(history_limit, 100))
        except Exception as e:
            self.log_sinker.pull_history_limit_failed(e)

    def _pull_and_inject_tasks(self) -> None:
        """从远程服务拉取任务注入信息并注入任务"""
        try:
            res = requests.get(
                f"{self.base_url}/api/pull_task_injection", timeout=self._pull_timeout()
            )
            if res.ok:
                injection_tasks: list[dict] = res.json()
                for injection in injection_tasks:
                    target_stage = injection.get("node")
                    task_datas = injection.get("task_datas")

                    # 这里你可以按需注入到不同的节点
                    task_datas = [
                        task if task != "TERMINATION_SIGNAL" else TERMINATION_SIGNAL
                        for task in task_datas
                    ]
                    try:
                        self.task_graph.put_stage_queue(
                            {target_stage: task_datas}, put_termination_signal=False
                        )
                        self.log_sinker.inject_tasks_success(target_stage, task_datas)
                    except Exception as e:
                        self.log_sinker.inject_tasks_failed(target_stage, task_datas, e)
        except Exception as e:
            self.log_sinker.pull_tasks_failed(e)

    def _push_errors(self) -> None:
        """推送错误信息"""
        try:
            if self._push_errors_mode == "meta":
                resp = self._push_errors_meta()
                if resp.get("ok"):
                    return
                if resp.get("fallback") == "need_content":
                    self._push_errors_mode = "content"

                raise RuntimeError(f"push_errors_meta failed: {resp.get('msg')}")

            elif self._push_errors_mode == "content":
                resp = self._push_errors_content()
                if resp.get("ok"):
                    return

                raise RuntimeError(f"push_errors_content failed: {resp.get('msg')}")

        except Exception as e:
            self.log_sinker.push_errors_failed(e)

    def _push_errors_meta(self) -> dict:
        """推送错误元信息"""
        jsonl_path = self.task_graph.get_fallback_path()
        rev = self.task_graph.fail_listener.total_error_num

        payload = {
            "jsonl_path": jsonl_path,
            "rev": rev,
        }
        response = requests.post(
            f"{self.base_url}/api/push_errors_meta",
            json=payload,
            timeout=self._push_timeout(),
        )
        return response.json()

    def _push_errors_content(self) -> dict:
        """推送错误内容"""
        jsonl_path = self.task_graph.get_fallback_path()
        rev = self.task_graph.fail_listener.total_error_num

        error_store = load_jsonl_logs(
            path=jsonl_path,
            keys=["ts", "error_id", "error_repr", "stage", "task_repr"],
        )
        payload = {
            "errors": error_store,
            "jsonl_path": jsonl_path,
            "rev": rev,
        }
        response = requests.post(
            f"{self.base_url}/api/push_errors_content",
            json=payload,
            timeout=self._push_timeout(),
        )
        return response.json()

    def _push_status(self) -> None:
        """推送状态信息"""
        try:
            self.task_graph.collect_runtime_snapshot()
            status_data = self.task_graph.get_status_dict()
            payload = {"status": status_data}
            requests.post(
                f"{self.base_url}/api/push_status",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_sinker.push_status_failed(e)

    def _push_structure(self) -> None:
        """推送结构信息"""
        try:
            structure = self.task_graph.get_structure_json()
            payload = {"items": structure}
            requests.post(
                f"{self.base_url}/api/push_structure",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_sinker.push_structure_failed(e)

    def _push_topology(self) -> None:
        """推送拓扑信息"""
        try:
            topology = self.task_graph.get_graph_topology()
            payload = {"topology": topology}
            requests.post(
                f"{self.base_url}/api/push_topology",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_sinker.push_topology_failed(e)

    def _push_summary(self) -> None:
        """推送摘要信息"""
        try:
            summary = self.task_graph.get_graph_summary()
            payload = {"summary": summary}
            requests.post(
                f"{self.base_url}/api/push_summary",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_sinker.push_summary_failed(e)

    def _push_history(self) -> None:
        """推送历史信息"""
        try:
            history = self.task_graph.get_stage_history()
            payload = {"history": history}
            requests.post(
                f"{self.base_url}/api/push_history",
                json=payload,
                timeout=self._push_timeout(),
            )
        except Exception as e:
            self.log_sinker.push_history_failed(e)


class NullTaskReporter:
    interval = 0

    def start(self) -> None:
        """启动上报器线程"""
        return None

    def stop(self) -> None:
        """停止上报器线程"""
        return None
