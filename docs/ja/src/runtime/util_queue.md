# util_queue

`runtime/util_queue.py` はマルチプロセスキューのクリーンアップユーティリティ関数を提供します。

## cleanup_mpqueue

```python
def cleanup_mpqueue(queue: MPQueue) -> None:
    """
    マルチプロセスキュー（multiprocessing.Queue）をドレインして閉じます。
    プロセス終了時にリソースを解放し、BrokenPipeError を回避するために使用されます。
    """
```

通常、プロセスの終了時または異常終了時に呼び出され、マルチプロセスキュー内の残留データを破棄し、キューを正しく閉じて join することを保証します。
