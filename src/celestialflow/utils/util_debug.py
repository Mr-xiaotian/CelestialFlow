# utils/util_debug.py
import pickle


def find_unpickleable(obj):
    try:
        pickle.dumps(obj)
        return False
    except Exception:
        return True
