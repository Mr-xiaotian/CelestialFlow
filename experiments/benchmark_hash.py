import timeit
import hashlib
import pickle
import json
import uuid

from celestialflow import format_table

# 测试对象（中等复杂度）
test_obj = {
    "name": "task",
    "params": {"a": 1, "b": [1, 2, 3], "c": {"d": 4}},
    "timestamp": 1710000000,
    "active": True
}

def method_1_pickle_hash():
    obj_bytes = pickle.dumps(test_obj)
    return hashlib.md5(obj_bytes).hexdigest()

def method_2_json_hash():
    obj_str = json.dumps(test_obj, sort_keys=True)
    return hashlib.sha256(obj_str.encode()).hexdigest()

def method_3_simple_str():
    return str(test_obj).replace(" ", "").replace("\n", "")

def method_4_uuid_hash():
    h = hashlib.sha1(repr(test_obj).encode()).digest()[:16]
    return str(uuid.UUID(bytes=h))


if __name__ == "__main__":
    # 定义测试次数
    iterations = 10000

    # 计时
    results = [
        [timeit.timeit(method_1_pickle_hash, number=iterations)],
        [timeit.timeit(method_2_json_hash, number=iterations)],
        [timeit.timeit(method_3_simple_str, number=iterations)],
        [timeit.timeit(method_4_uuid_hash, number=iterations)],
    ]
    modes = ['pickle+md5', 'json+sha256', 'simple str', 'uuid+sha1']

    print(format_table(results, modes, ["Hashing Methods Benchmark"]))
