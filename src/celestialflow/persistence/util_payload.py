# persistence/util_payload.py
from typing import Any, cast


def to_persisted_payload(task: Any) -> Any:
    """
    将任务转换为可持久化的 JSON 友好结构。

    :param task: 失败任务
    :return: 可持久化的 JSON 友好结构
    :raises: 任务类型不支持时抛出异常
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
