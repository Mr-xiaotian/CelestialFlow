# util_queue

`runtime/util_queue.py` 提供多进程队列的清理工具函数。

## cleanup_mpqueue

```python
def cleanup_mpqueue(queue: MPQueue) -> None:
    """
    清空并关闭一个多进程队列（multiprocessing.Queue），
    用于在进程退出时释放资源、避免 BrokenPipeError。
    """
```

通常在流程终止或异常退出时调用，确保多进程队列中的残留数据被丢弃，队列被正确关闭和 join。
