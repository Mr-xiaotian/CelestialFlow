# SuccessSpout

> 📅 最終更新日: 2026/04/24

`SuccessSpout` は `BaseSpout` を継承し、成功結果キューを継続的に監視して task-result ペアをキャッシュします。

## 初期化

```python
class SuccessSpout(BaseSpout):
    def __init__(self):
        super().__init__()
        self.success_pairs: list[tuple[Any, Any]] = []
```

## コアメソッド

### get_success_pairs

```python
def get_success_pairs(self) -> list[tuple[Any, Any]]:
    """
    成功したタスクと結果のペアリストを取得する。

    :return: [(task, result), ...]
    """
```

## 内部実装

### _handle_record

キューから `TaskEnvelope` を受信し、元のタスク（`record.prev`）と結果（`record.task`）を抽出して `success_pairs` に追加します。

### _before_start

開始前に `success_pairs` をクリアします。

## 使用シーン

成功結果は `SuccessSpout` のキューに送信されます。実行完了後、`get_success_pairs()` ですべての成功した (task, result) ペアを取得できます。

```python
executor = TaskExecutor("Processor", process)
executor.start(tasks)
pairs = executor.get_success_pairs()
```
