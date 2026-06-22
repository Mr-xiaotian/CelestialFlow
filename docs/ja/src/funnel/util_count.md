# PendingCounter

> 📅 最終更新日: 2026/06/22

`funnel/util_count.py` は、スレッドセーフな待処理カウンター `PendingCounter` を提供します。これは、ある `BaseSpout` に対応するレコードのうち、まだ処理が完了していない数を統計するために使用されます。

## コアオブジェクト

### PendingCounter

```python
class PendingCounter:
    def __init__(self) -> None: ...
    def increment(self) -> int: ...
    def decrement(self) -> int: ...
    def get_count(self) -> int: ...
```

`PendingCounter` は内部で `threading.Lock` を使用してカウンタ変数を保護しているため、マルチスレッド環境でも安全に使用できます。

## メソッド説明

| メソッド | 戻り値 | 説明 |
|------|--------|------|
| `increment()` | `int` | 待処理数を 1 増やし、増加後の値を返す |
| `decrement()` | `int` | 待処理数を 1 減らし、減少後の値を返す |
| `get_count()` | `int` | 現在の待処理数を読み取る |

## 使用方式

`PendingCounter` は通常、`BaseSpout` の初期化時に自動的に作成され、ユーザーが直接操作する必要はありません。`BaseSpout.get_counter()` と `BaseSpout.get_pending_count()` が外部からのアクセス入口を提供します：

```python
from celestialflow.funnel import BaseSpout

class PrintSpout(BaseSpout):
    def _handle_record(self, record):
        print(record)

spout = PrintSpout()
spout.start()

spout.get_queue().put("task_1")
spout.get_queue().put("task_2")

print(f"待処理: {spout.get_pending_count()}")

spout.stop()
print(f"停止後待処理: {spout.get_pending_count()}")
```

## 注意事項

1. **統計口径**：`BaseSpout._spout()` は、レコードをデキューした後に `_handle_record()` を呼び出し、処理が完了（例外を含む）してから `decrement()` を呼び出すため、`get_pending_count()` には「デキュー済みだがまだ処理中」のレコードも含まれます。
2. **ロールバック機構**：`BaseInlet._funnel()` は、エンキュー前に `increment()` を呼び出し、エンキューに失敗すると即座に `decrement()` を呼び出してカウンタをロールバックします。
3. **スレッドセーフ**：すべての操作は `Lock` によって保護されており、複数プロデューサー・単一コンシューマーのシナリオでも安全に使用できます。
