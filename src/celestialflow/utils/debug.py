# utils/debug.py
import pickle


def find_unpickleable(name, obj):
    try:
        pickle.dumps(obj)
        return True
    except Exception as e:
        print("[UNPICKLABLE]", name, type(obj), e)
        return False
