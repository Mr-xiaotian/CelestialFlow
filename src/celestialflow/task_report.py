from threading import Event, Thread
from typing import List

import requests

from .task_logging import TaskLogger
from .task_tools import load_jsonl_logs
from .task_types import TERMINATION_SIGNAL


class TaskReporter:
    """
    周期性向远程服务推送任务运行状态的上报器。

    - 定时从服务器拉取配置（如上报间隔、任务注入信息）
    - 将任务图中的状态、错误、结构、拓扑等信息推送到后端接口
    - 以后台线程方式运行，可随时 start()/stop()
    - 主要用于可视化监控、任务远程控制与 Web UI 同步
    """

    def __init__(self, task_graph, log_queue, log_level, host="127.0.0.1", port=5000):
        from .task_graph import TaskGraph

        self.task_graph: TaskGraph = task_graph
        self.logger = TaskLogger(log_queue, log_level)
        self.base_url = f"http://{host}:{port}"

        self._stop_flag = Event()
        self._thread = None
        self._push_errors_mode = "meta"

        self.interval = 5

    def start(self):
        if self._thread is None or not self._thread.is_alive():
            self._stop_flag.clear()
            self._thread = Thread(target=self._loop, daemon=True)
            self._thread.start()

    def stop(self):
        if self._thread:
            self._refresh_all()  # 最后一次
            self._stop_flag.set()
            self._thread.join(timeout=2)
            self._thread = None
            self.logger.stop_reporter()

    def _pull_timeout(self) -> float:
        return max(1.0, min(self.interval * 0.2, 5.0))

    def _push_timeout(self) -> float:
        return max(1.0, min(self.interval * 0.2, 3.0))

    def _loop(self):
        while not self._stop_flag.is_set():
            try:
                self._refresh_all()
            except Exception as e:
                self.logger.loop_failed(e)
            self._stop_flag.wait(self.interval)

    def _refresh_all(self):
        # 拉取逻辑
        self._pull_interval()
        self._pull_and_inject_tasks()

        # 推送逻辑
        self._push_errors()
        self._push_status()
        self._push_structure()
        self._push_topology()

    def _pull_interval(self):
        try:
            res = requests.get(f"{self.base_url}/api/get_interval", timeout=self._pull_timeout())
            if res.ok:
                interval = res.json().get("interval", 5)
                self.interval = max(1.0, min(interval, 60.0))
        except Exception as e:
            self.logger.pull_interval_failed(e)

    def _pull_and_inject_tasks(self):
        try:
            res = requests.get(f"{self.base_url}/api/get_task_injection", timeout=self._pull_timeout())
            if res.ok:
                tasks_list: List[dict] = res.json()
                for task in tasks_list:
                    target_node = task.get("node")
                    task_datas = task.get("task_datas")

                    # 这里你可以按需注入到不同的节点
                    task_datas = [
                        task if task != "TERMINATION_SIGNAL" else TERMINATION_SIGNAL
                        for task in task_datas
                    ]
                    try:
                        self.task_graph.put_stage_queue(
                            {target_node: task_datas}, put_termination_signal=False
                        )
                        self.logger.inject_tasks_success(target_node, task_datas)
                    except Exception as e:
                        self.logger.inject_tasks_failed(target_node, task_datas, e)
        except Exception as e:
            self.logger.pull_tasks_failed(e)

    def _push_errors(self):
        try:
            self.task_graph.handle_fail_queue()

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
            self.logger.push_errors_failed(e)

    def _push_errors_meta(self) -> dict:
        jsonl_path = self.task_graph.get_error_jsonl_path()
        rev = self.task_graph.total_error_num

        payload = {
            "jsonl_path": jsonl_path,
            "rev": rev,
        }
        response = requests.post(
            f"{self.base_url}/api/push_errors_meta", json=payload, timeout=self._push_timeout()
        )
        return response.json()

    def _push_errors_content(self) -> dict:
        jsonl_path = self.task_graph.get_error_jsonl_path()
        rev = self.task_graph.total_error_num

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
            f"{self.base_url}/api/push_errors_content", json=payload, timeout=self._push_timeout()
        )
        return response.json()

    def _push_status(self):
        try:
            status_data = self.task_graph.get_status_dict()
            payload = {"status": status_data}
            requests.post(f"{self.base_url}/api/push_status", json=payload, timeout=self._push_timeout())
        except Exception as e:
            self.logger.push_status_failed(e)

    def _push_structure(self):
        try:
            structure = self.task_graph.get_structure_json()
            payload = {"items": structure}
            requests.post(
                f"{self.base_url}/api/push_structure", json=payload, timeout=self._push_timeout()
            )
        except Exception as e:
            self.logger.push_structure_failed(e)

    def _push_topology(self):
        try:
            topology = self.task_graph.get_graph_topology()
            payload = {"topology": topology}
            requests.post(f"{self.base_url}/api/push_topology", json=payload, timeout=self._push_timeout())
        except Exception as e:
            self.logger.push_topology_failed(e)


class NullTaskReporter:
    interval = 0

    def start(self):
        return None

    def stop(self):
        return None
