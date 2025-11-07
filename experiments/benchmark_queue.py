import time
from queue import Queue as ThreadQueue
from multiprocessing import Queue as MPQueue
from multiprocessing import Manager
import redis


def test_threadqueue_perf(count):
    q = ThreadQueue()

    start_put = time.time()
    for i in range(count):
        q.put(i)
    put_duration = time.time() - start_put

    start_get = time.time()
    for _ in range(count):
        q.get()
    get_duration = time.time() - start_get

    start_size = time.time()
    for _ in range(count):
        _ = q.qsize()
    size_duration = time.time() - start_size

    start_empty = time.time()
    for _ in range(count):
        _ = q.empty()
    empty_duration = time.time() - start_empty

    print(f"\nThreadQueue ({count} items):")
    print(f"  put:    {put_duration:.4f}s")
    print(f"  get:    {get_duration:.4f}s")
    print(f"  qsize:  {size_duration:.6f}s ")
    print(f"  empty:  {empty_duration:.6f}s")


def test_mpqueue_perf(count):
    q = MPQueue()

    start_put = time.time()
    for i in range(count):
        q.put(i)
    put_duration = time.time() - start_put

    start_get = time.time()
    for _ in range(count):
        q.get()
    get_duration = time.time() - start_get

    start_size = time.time()
    for _ in range(count):
        _ = q.qsize()
    size_duration = time.time() - start_size

    start_empty = time.time()
    for _ in range(count):
        _ = q.empty()
    empty_duration = time.time() - start_empty

    print(f"\nMPQueue ({count} items):")
    print(f"  put:    {put_duration:.4f}s")
    print(f"  get:    {get_duration:.4f}s")
    print(f"  qsize:  {size_duration:.6f}s ")
    print(f"  empty:  {empty_duration:.6f}s")


def test_manager_queue_perf(count):
    with Manager() as manager:
        q = manager.Queue()

        start_put = time.time()
        for i in range(count):
            q.put(i)
        put_duration = time.time() - start_put

        start_get = time.time()
        for _ in range(count):
            q.get()
        get_duration = time.time() - start_get

        start_size = time.time()
        for _ in range(count):
            _ = q.qsize()
        size_duration = time.time() - start_size

        start_empty = time.time()
        for _ in range(count):
            _ = q.empty()
        empty_duration = time.time() - start_empty

    print(f"\nManager().Queue ({count} items):")
    print(f"  put:    {put_duration:.4f}s")
    print(f"  get:    {get_duration:.4f}s")
    print(f"  qsize:  {size_duration:.6f}s ")
    print(f"  empty:  {empty_duration:.6f}s")


def test_redis_list_perf(r, count):
    key = "redis_queue"
    r.delete(key)

    start_put = time.time()
    for i in range(count):
        r.lpush(key, i)
    put_duration = time.time() - start_put

    start_get = time.time()
    for _ in range(count):
        r.rpop(key)
    get_duration = time.time() - start_get

    start_size = time.time()
    for _ in range(count):
        _ = r.llen(key)
    size_duration = time.time() - start_size

    start_empty = time.time()
    for _ in range(count):
        _ = r.llen(key) == 0
    empty_duration = time.time() - start_empty

    print(f"\nRedis List ({count} items):")
    print(f"  lpush:  {put_duration:.4f}s")
    print(f"  rpop:   {get_duration:.4f}s")
    print(f"  llen:   {size_duration:.6f}s")
    print(f"  empty:  {empty_duration:.6f}s")


def test_redis_stream_perf(r, count):
    key = "redis_stream"
    r.delete(key)

    start_put = time.time()
    for i in range(count):
        r.xadd(key, {"data": i})
    put_duration = time.time() - start_put

    last_id = "0-0"
    start_get = time.time()
    total_read = 0
    while total_read < count:
        messages = r.xread({key: last_id}, count=1000, block=0)
        if messages:
            for stream_key, msgs in messages:
                for msg_id, fields in msgs:
                    last_id = msg_id
                    total_read += 1
    get_duration = time.time() - start_get

    start_size = time.time()
    for _ in range(count):
        _ = r.xlen(key)
    size_duration = time.time() - start_size

    start_empty = time.time()
    for _ in range(count):
        _ = r.xlen(key) == 0
    empty_duration = time.time() - start_empty

    print(f"\nRedis Stream ({count} items):")
    print(f"  xadd:   {put_duration:.4f}s")
    print(f"  xread:  {get_duration:.4f}s")
    print(f"  xlen:   {size_duration:.6f}s")
    print(f"  empty:  {empty_duration:.6f}s")


if __name__ == "__main__":
    COUNT = 100_000
    print(f"Running benchmarks with {COUNT} items...")

    # Thread queue benchmark
    test_threadqueue_perf(COUNT)

    # Multiprocessing queue benchmark
    test_mpqueue_perf(COUNT)

    # Manager queue benchmark
    test_manager_queue_perf(COUNT)
    
    # Redis benchmarks (if redis server exists)
    try:
        redis_client = redis.Redis(decode_responses=True)
        redis_client.ping()
        redis_client.flushdb()

        test_redis_list_perf(redis_client, COUNT)
        test_redis_stream_perf(redis_client, COUNT)

    except Exception as e:
        print("\n⚠️ Redis tests skipped:")
        print(f"   {e}")
