import time, os
import queue
import redis
import threading
import multiprocessing
from multiprocessing import Manager, Process, Value
from dotenv import load_dotenv

N = 10000

load_dotenv()
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_passward = os.getenv("REDIS_PASSWORD")

# =======================
# Worker functions (must be global for Windows)
# =======================


def mpqueue_worker(q):
    t0 = time.time()
    for i in range(N):
        q.put(i)
    t1 = time.time()
    for i in range(N):
        _ = q.get()
    t2 = time.time()
    print(f"MPQueue: put={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def manager_dict_worker(d):
    t0 = time.time()
    for i in range(N):
        d[i] = i
    t1 = time.time()
    for i in range(N):
        _ = d[i]
    t2 = time.time()
    print(f"Manager.dict: put={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def value_worker(val):
    t0 = time.time()
    for _ in range(N):
        with val.get_lock():
            val.value += 1
    t1 = time.time()
    print(f"Value (number): inc={t1 - t0:.4f}s")


# =======================
# Redis connection helper
# =======================


def get_redis_connection():
    try:
        r = redis.Redis(host=redis_host, port=redis_port, db=0, password=redis_passward, decode_responses=True)
        r.ping()
        return r
    except Exception as e:
        print(f"\n⚠️ Redis not available, skipping Redis tests: {e}")
        return None


# =======================
# Tests
# =======================


def test_builtin_dict():
    d = {}
    t0 = time.time()
    for i in range(N):
        d[i] = i
    t1 = time.time()
    for i in range(N):
        _ = d[i]
    t2 = time.time()
    print(f"Built-in dict: put={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def test_queue_thread():
    q = queue.Queue()
    t0 = time.time()
    for i in range(N):
        q.put(i)
    t1 = time.time()
    for i in range(N):
        _ = q.get()
    t2 = time.time()
    print(f"Queue (thread): put={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def test_mpqueue():
    q = multiprocessing.Queue()
    p = Process(target=mpqueue_worker, args=(q,))
    p.start()
    p.join()


def test_manager_dict():
    with Manager() as manager:
        d = manager.dict()
        p = Process(target=manager_dict_worker, args=(d,))
        p.start()
        p.join()


def test_value_number():
    v = Value("i", 0)
    p = Process(target=value_worker, args=(v,))
    p.start()
    p.join()


def test_redis_plain(r):
    t0 = time.time()
    for i in range(N):
        r.set(f"plain_key{i}", i)
    t1 = time.time()
    for i in range(N):
        _ = r.get(f"plain_key{i}")
    t2 = time.time()
    print(f"Redis (plain): set={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def test_redis_pipeline(r):
    t0 = time.time()
    pipe = r.pipeline()
    for i in range(N):
        pipe.set(f"pipe_key{i}", i)
    pipe.execute()
    t1 = time.time()

    pipe = r.pipeline()
    for i in range(N):
        pipe.get(f"pipe_key{i}")
    _ = pipe.execute()
    t2 = time.time()

    print(f"Redis (pipeline): set={t1 - t0:.4f}s, get={t2 - t1:.4f}s")


def test_redis_multithread_plain(r, num_threads=10):
    count_per_thread = N // num_threads
    threads = []

    def writer(tid, base):
        for i in range(count_per_thread):
            r.set(f"mt_key{tid}_{i+base}", i)

    t0 = time.time()
    for t_id in range(num_threads):
        base = t_id * count_per_thread
        thread = threading.Thread(target=writer, args=(t_id, base))
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()
    t1 = time.time()

    threads = []

    def reader(tid, base):
        for i in range(count_per_thread):
            _ = r.get(f"mt_key{tid}_{i+base}")

    for t_id in range(num_threads):
        base = t_id * count_per_thread
        thread = threading.Thread(target=reader, args=(t_id, base))
        thread.start()
        threads.append(thread)

    for t in threads:
        t.join()
    t2 = time.time()

    print(
        f"Redis (multi-thread x{num_threads}, no pipeline): set={t1 - t0:.4f}s, get={t2 - t1:.4f}s"
    )


def test_redis_hash(r):
    t0 = time.time()
    for i in range(N):
        r.hset("hash_test", f"field{i}", i)
    t1 = time.time()
    for i in range(N):
        _ = r.hget("hash_test", f"field{i}")
    t2 = time.time()
    print(f"Redis (hash): hset={t1 - t0:.4f}s, hget={t2 - t1:.4f}s")


def test_redis_list(r):
    r.delete("list_test")
    t0 = time.time()
    for i in range(N):
        r.rpush("list_test", i)
    t1 = time.time()
    for i in range(N):
        _ = r.lindex("list_test", i)
    t2 = time.time()
    print(f"Redis (list): rpush={t1 - t0:.4f}s, lindex={t2 - t1:.4f}s")


def test_redis_set(r):
    r.delete("set_test")
    t0 = time.time()
    for i in range(N):
        r.sadd("set_test", i)
    t1 = time.time()
    for i in range(N):
        _ = r.sismember("set_test", i)
    t2 = time.time()
    print(f"Redis (set): sadd={t1 - t0:.4f}s, sismember={t2 - t1:.4f}s")


def test_redis_zset(r):
    r.delete("zset_test")
    t0 = time.time()
    for i in range(N):
        r.zadd("zset_test", {f"item{i}": i})
    t1 = time.time()
    for i in range(N):
        _ = r.zscore("zset_test", f"item{i}")
    t2 = time.time()
    print(f"Redis (zset): zadd={t1 - t0:.4f}s, zscore={t2 - t1:.4f}s")


# =======================
# Main Runner
# =======================

if __name__ == "__main__":
    print(f"\nRunning benchmarks with N={N}\n")

    test_builtin_dict()
    test_queue_thread()
    test_mpqueue()
    test_manager_dict()
    test_value_number()

    r = get_redis_connection()
    if r:
        test_redis_plain(r)
        test_redis_pipeline(r)
        test_redis_multithread_plain(r)
        test_redis_hash(r)
        test_redis_list(r)
        test_redis_set(r)
        test_redis_zset(r)
