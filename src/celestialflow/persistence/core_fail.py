# persistence/core_fail.py
import json
from pathlib import Path
from datetime import datetime

from ..utils.util_format import format_repr
from .core_base import BaseListener, BaseSinker


class FailListener(BaseListener):
    def __init__(self, error_source: str):
        super().__init__()

        self.error_source = error_source
        self.fail_queue = self.queue
        self.jsonl_path: Path | None = None

        self.total_error_num = 0
        self._file = None

    def _before_start(self):
        # 创建 fallback 目录
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H-%M-%S-%f")[:-3]
        self.jsonl_path = Path(
            f"./fallback/{date_str}/{self.error_source}({time_str}).jsonl"
        )
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)

        # 打开失败记录文件
        self._file = self.jsonl_path.open("a", encoding="utf-8")

        # 初始化错误计数器
        self.total_error_num = 0

    def _handle_record(self, record):
        jsonl_record = json.dumps(record, ensure_ascii=False)

        self._file.write(f"{jsonl_record}\n")
        self._file.flush()

        if isinstance(record, dict) and record.get("error_id") is not None:
            self.total_error_num += 1

    def _after_stop(self):
        if self._file:
            self._file.flush()
            self._file.close()
            self._file = None


class FailSinker(BaseSinker):
    """
    多进程安全失败记录包装类，所有失败记录通过队列发送到监听进程写入
    """

    def __init__(self, fail_queue):
        super().__init__(fail_queue)
        self.fail_queue = self.queue

    def start_graph(self, structure_json):
        """
        在运行开始时写入任务结构元信息到 jsonl 文件
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "structure": structure_json,
        }
        self._sink(meta_item)

    def start_executor(self, executor_tag: str):
        """
        在运行开始时写入执行器元信息到 jsonl 文件
        """
        meta_item = {
            "timestamp": datetime.now().isoformat(),
            "executor": executor_tag,
        }
        self._sink(meta_item)

    def task_error(self, stage_tag, error, err_id, task):
        """
        写入错误日志到 jsonl 文件中

        :param stage_tag: 阶段标签
        :param error: 错误信息
        :param err_id: 错误ID
        :param task: 任务字符串
        """
        now = datetime.now()
        error_message = f"{type(error).__name__}({error})"
        fail_item = {
            "timestamp": now.isoformat(),
            "stage": stage_tag,
            "error_repr": format_repr(error_message, 100),
            "task_repr": format_repr(task, 100),
            "error": error_message,
            "task": task,
            "error_id": err_id,
            "ts": now.timestamp(),
        }
        self._sink(fail_item)
