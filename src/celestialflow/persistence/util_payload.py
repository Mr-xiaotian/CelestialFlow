# persistence/util_payload.py
from typing import Any, cast


def to_persisted_payload(task: Any) -> Any:
    """
    将任务转换为可持久化的 JSON 友好结构。

    基本类型原样保留，容器类型递归转换，其他类型回退为字符串。

    :param task: 失败任务
    :return: 可持久化的 JSON 友好结构
    """
    if task is None or isinstance(task, str | int | float | bool):
        return task
    if isinstance(task, list | tuple | set):
        iterable_task = cast(list[Any] | tuple[Any, ...] | set[Any], task)
        items = list(iterable_task)
        return [to_persisted_payload(item) for item in items]
    if isinstance(task, dict):
        task_dict = cast(dict[Any, Any], task)
        return {
            str(key): to_persisted_payload(value) for key, value in task_dict.items()
        }
    return str(task)
