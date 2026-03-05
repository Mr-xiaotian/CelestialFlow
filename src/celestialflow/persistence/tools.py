import json
from typing import Any
from pathlib import Path
from collections.abc import Iterable
from multiprocessing import Queue as MPQueue


# ======== 队列处理 ========
def cleanup_mpqueue(queue: MPQueue):
    """
    清理队列
    """
    queue.close()
    queue.join_thread()  # 确保队列的后台线程正确终止


# ======== jsonl文件处理 ========
def append_jsonl_log(log_data: dict, file_path: str, logger=None):
    """
    将日志字典写入指定目录下的 JSONL 文件。

    :param log_data: 要写入的日志项（字典）
    :param start_time: 运行开始时间，用于构造路径
    :param base_path: 基础路径，例如 './fallback'
    :param prefix: 文件名前缀，例如 'realtime_errors'
    :param logger: 可选的日志对象用于记录失败信息
    """
    try:
        file_path: Path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_data, ensure_ascii=False) + "\n")
    except Exception as e:
        if logger:
            logger._log("WARNING", f"[Persist] 写入日志失败: {e}")


def append_jsonl_logs(log_items: Iterable[dict], file_path: str, logger=None):
    """
    将多条日志一次性写入 JSONL 文件（batch 追加）。

    :param log_items: Iterable[dict]，每个元素写成一行 JSON
    :param file_path: JSONL 文件路径
    :param logger: 可选日志对象
    """
    try:
        if not isinstance(log_items, Iterable):
            raise TypeError("log_items must be an iterable of dict")

        file_path: Path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "a", encoding="utf-8") as f:
            for item in log_items:
                if not isinstance(item, dict):
                    raise TypeError(f"each log item must be dict, got {type(item)}")
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except Exception as e:
        if logger:
            logger._log("WARNING", f"[Persist] 批量写入日志失败: {e}")
