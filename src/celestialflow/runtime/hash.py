import hashlib
import pickle
from typing import Any


# ======== 处理hash任务 ========
def make_hashable(obj) -> Any:
    """
    把 obj 转换成可哈希的形式。
    """
    if isinstance(obj, (tuple, list)):
        return tuple(make_hashable(e) for e in obj)
    elif isinstance(obj, dict):
        # dict 转换成 (key, value) 对的元组，且按 key 排序以确保哈希结果一致
        return tuple(
            sorted((make_hashable(k), make_hashable(v)) for k, v in obj.items())
        )
    elif isinstance(obj, set):
        # set 转换成排序后的 tuple
        return tuple(sorted(make_hashable(e) for e in obj))
    else:
        # 基本类型直接返回
        return obj


def object_to_str_hash(obj) -> str:
    """
    将任意对象转换为 MD5 字符串。

    :param obj: 任意对象
    :return: MD5 字符串
    """
    obj_bytes = pickle.dumps(obj)  # 序列化对象
    return hashlib.md5(obj_bytes).hexdigest()