import gc
import hashlib
import json
import pickle
import statistics
import timeit
import uuid
from typing import Any, Callable

from celestialflow import format_table

# =========================
# 测试对象
# =========================
TEST_CASES = {
    "int": 123456789,
    "short_str": "celestialflow",
    "long_str_4k": "x" * 4096,
    "bytes_4k": b"x" * 4096,
    "small_tuple": (1, "a", 3.14, True, None),
    "small_list": [1, 2, 3, 4, 5],
    "list_100_ints": list(range(100)),
    "small_dict": {
        "name": "task",
        "params": {"a": 1, "b": [1, 2, 3], "c": {"d": 4}},
        "timestamp": 1710000000,
        "active": True,
    },
    "dict_100_pairs": {f"k{i}": i for i in range(100)},
    "nested_dict": {
        "meta": {
            "name": "task",
            "version": 3,
            "flags": [True, False, True],
        },
        "params": {
            "a": 1,
            "b": [1, 2, 3, {"x": 10, "y": [20, 30]}],
            "c": {"d": 4, "e": {"f": "hello", "g": None}},
        },
        "timestamp": 1710000000,
        "active": True,
    },
    "set_100_ints": set(range(100)),
}


# =========================
# 工具函数
# =========================
def normalize_for_hash(obj: Any) -> Any:
    """
    将常见容器转为稳定结构，便于 repr/json/hash。
    """
    if isinstance(obj, bytes):
        return {
            "__type__": "bytes",
            "hex": obj.hex(),
        }

    if isinstance(obj, tuple):
        return {
            "__type__": "tuple",
            "items": [normalize_for_hash(x) for x in obj],
        }

    if isinstance(obj, list):
        return {
            "__type__": "list",
            "items": [normalize_for_hash(x) for x in obj],
        }

    if isinstance(obj, dict):
        return {
            "__type__": "dict",
            "items": [
                [normalize_for_hash(k), normalize_for_hash(v)]
                for k, v in sorted(obj.items(), key=lambda kv: repr(kv[0]))
            ],
        }

    if isinstance(obj, set):
        return {
            "__type__": "set",
            "items": sorted(normalize_for_hash(x) for x in obj),
        }

    return obj


def stable_repr_bytes(obj: Any) -> bytes:
    normalized = normalize_for_hash(obj)
    return repr(normalized).encode("utf-8")


def stable_json_bytes(obj: Any) -> bytes:
    normalized = normalize_for_hash(obj)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


# =========================
# 候选 hash 方法
# =========================
def method_pickle_md5(obj: Any) -> str:
    return hashlib.md5(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()


def method_pickle_sha1(obj: Any) -> str:
    return hashlib.sha1(pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)).hexdigest()


def method_pickle_blake2b_16(obj: Any) -> str:
    return hashlib.blake2b(
        pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL),
        digest_size=16,
    ).hexdigest()


def method_json_md5(obj: Any) -> str:
    return hashlib.md5(stable_json_bytes(obj)).hexdigest()


def method_json_sha256(obj: Any) -> str:
    return hashlib.sha256(stable_json_bytes(obj)).hexdigest()


def method_repr_md5(obj: Any) -> str:
    return hashlib.md5(stable_repr_bytes(obj)).hexdigest()


def method_repr_sha1_uuid(obj: Any) -> str:
    h = hashlib.sha1(stable_repr_bytes(obj)).digest()[:16]
    return str(uuid.UUID(bytes=h))


def method_repr_blake2b_16(obj: Any) -> str:
    return hashlib.blake2b(stable_repr_bytes(obj), digest_size=16).hexdigest()


def method_fast_mixed(obj: Any) -> str:
    """
    将任意对象转换为稳定的哈希字符串。

    策略：
    - bytes: 直接哈希原始字节
    - str: UTF-8 编码后直接哈希
    - int / float / bool / None: 对 repr 后的字节直接哈希
    - 其他对象: 使用 pickle 序列化后再哈希

    :param obj: 任意对象
    :return: 哈希字符串
    """
    if isinstance(obj, bytes):
        data = obj
    elif isinstance(obj, str):
        data = obj.encode("utf-8")
    elif isinstance(obj, (int, float, bool, type(None))):
        data = repr(obj).encode("utf-8")
    else:
        data = pickle.dumps(obj, protocol=pickle.HIGHEST_PROTOCOL)

    return hashlib.sha1(data).hexdigest()


METHODS: dict[str, Callable[[Any], str]] = {
    "pickle+md5": method_pickle_md5,
    "pickle+sha1": method_pickle_sha1,
    "pickle+blake2b16": method_pickle_blake2b_16,
    "json+md5": method_json_md5,
    "json+sha256": method_json_sha256,
    "repr+md5": method_repr_md5,
    "repr+sha1+uuid": method_repr_sha1_uuid,
    "repr+blake2b16": method_repr_blake2b_16,
    "fast_mixed": method_fast_mixed,
}


# =========================
# Benchmark 核心
# =========================
def benchmark_one(
    func: Callable[[Any], str], obj: Any, repeat: int = 7, number: int = 10000
) -> tuple[float, float]:
    """
    返回:
    - 平均每次耗时（微秒）
    - 标准差（微秒）
    """
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        samples = timeit.repeat(lambda: func(obj), repeat=repeat, number=number)
    finally:
        if gc_was_enabled:
            gc.enable()

    per_call_us = [s / number * 1_000_000 for s in samples]
    return statistics.mean(per_call_us), (
        statistics.stdev(per_call_us) if len(per_call_us) > 1 else 0.0
    )


def verify_methods() -> None:
    """
    简单校验每个方法都能对所有 case 跑通。
    """
    for case_name, obj in TEST_CASES.items():
        for method_name, func in METHODS.items():
            try:
                result = func(obj)
                if not isinstance(result, str):
                    raise TypeError(f"Result is not str: {type(result)}")
            except Exception as e:
                raise RuntimeError(f"[{case_name}] [{method_name}] failed: {e}") from e


def run_benchmark() -> None:
    verify_methods()

    for case_name, obj in TEST_CASES.items():
        rows = []
        best_mean = None

        raw_results = []
        for method_name, func in METHODS.items():
            mean_us, std_us = benchmark_one(func, obj)
            raw_results.append((method_name, mean_us, std_us))
            if best_mean is None or mean_us < best_mean:
                best_mean = mean_us

        for method_name, mean_us, std_us in raw_results:
            ratio = mean_us / best_mean if best_mean else 1.0
            rows.append(
                [
                    f"{mean_us:.3f} us",
                    f"{std_us:.3f} us",
                    f"{ratio:.2f}x",
                ]
            )

        print(f"\n=== Case: {case_name} ===")
        print(
            format_table(
                rows,
                list(METHODS.keys()),
                ["mean", "std", "vs_best"],
            )
        )


if __name__ == "__main__":
    run_benchmark()
