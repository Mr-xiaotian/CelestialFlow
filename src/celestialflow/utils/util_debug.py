# utils/util_debug.py
import pickle


def find_unpickleable(obj):
    """
    检测对象是否不可 pickle 序列化

    :param obj: 待检测的对象
    :return: 如果不可序列化返回 True，否则返回 False
    """
    try:
        pickle.dumps(obj)
        return False
    except Exception:
        return True
