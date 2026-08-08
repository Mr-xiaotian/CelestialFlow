# runtime/util_hash.py
import hashlib
import pickle
from typing import Any, cast


# ==== 哈希工具 ====
def make_hashable(obj: Any) -> Any:
    """
    把 obj 转换成可哈希的形式。

    :param obj: 任意对象
    :return: 可哈希的等价形式
    """
    if isinstance(obj, tuple | list):
        return tuple(make_hashable(e) for e in cast(list[Any], obj))
    elif isinstance(obj, dict):
        # 将字典转换成按 key 排序的 (key, value) 元组，保证哈希结果稳定
        obj_dict = cast(dict[Any, Any], obj)
        return tuple(
            sorted((make_hashable(k), make_hashable(v)) for k, v in obj_dict.items())
        )
    elif isinstance(obj, set):
        # 将集合转换成排序后的元组
        return tuple(sorted(make_hashable(e) for e in cast(set[Any], obj)))
    else:
        # 基本类型直接返回
        return obj


def object_to_hash(obj: Any) -> bytes:
    """
    将任意对象转换为 SHA1 字节串。

    :param obj: 任意对象
    :return: SHA1 字节串
    """
    obj_bytes = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)
    return hashlib.sha1(obj_bytes).digest()
