# funnel_scope

> 📅 最終更新日: 2026/08/26

`persistence/core_scope.py` は、グローバルな funnel のライフサイクルを管理するコンテキストマネージャ `funnel_scope` を提供し、`LifecycleSpout` と `LogSpout` の起動と停止を統一的に扱います。

## 中核オブジェクト

### funnel_scope

```python
@contextmanager
def funnel_scope() -> Generator[None, None, None]:
```

単層のコンテキストマネージャであり、以下を担当します：

1. スコープ進入時にグローバルな `LifecycleSpout` と `LogSpout` を順に起動する
2. スコープ退出時に `LogSpout` と `LifecycleSpout` の順に停止する
3. 進入と退出の過程で発生するすべての例外を収集し、`ExceptionGroup` として一括で送出する

```python
from celestialflow.persistence import funnel_scope

with funnel_scope():
    # LifecycleSpout と LogSpout が起動済み
    # ビジネスロジックを実行...
    ...
# スコープ退出時に両 Spout が停止済み
```

## 注意事項

1. **単層スコープ**：現在の実装はネストされたスコープの再利用セマンティクスを保証しません。`funnel_scope` は毎回独立して使用してください。
2. **例外処理**：進入または退出の過程で発生した例外はリストに収集され、最終的に `ExceptionGroup` として送出されます。例外情報は失われません。
3. **停止順序**：`LogSpout` を先に停止し、その後 `LifecycleSpout` を停止することで、ログが可能な限り完全に残るよう保証します。
