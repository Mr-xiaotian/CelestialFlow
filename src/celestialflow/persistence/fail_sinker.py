from datetime import datetime
from multiprocessing import Queue as MPQueue

from .tools import format_repr


class FailSinker:
    """
    多进程安全失败记录包装类，所有失败记录通过队列发送到监听进程写入
    """

    def __init__(self, fail_queue):
        self.fail_queue: MPQueue = fail_queue

    def _sink(self, record: dict):
        self.fail_queue.put(record)

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

    def task_error(self, ts, stage_tag, error, err_id, task):
        """
        写入错误日志到 jsonl 文件中

        :param ts: 错误时间戳
        :param stage_tag: 阶段标签
        :param error: 错误信息
        :param err_id: 错误ID
        :param task: 任务字符串
        """
        error_message = f"{type(error).__name__}({error})"
        fail_item =  {
                "timestamp": datetime.fromtimestamp(ts).isoformat(),
                "stage": stage_tag,
                "error_repr": format_repr(error_message, 100),
                "task_repr": format_repr(task, 100),
                "error": error_message,
                "task": task,
                "error_id": err_id,
                "ts": ts,
            }
        self._sink(fail_item)
