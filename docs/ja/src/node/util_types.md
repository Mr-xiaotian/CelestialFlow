# AnyTaskNode

> 📅 最終更新日: 2026/09/09

`util_types.py` は `node` モジュールにノード層特有の型エイリアスを提供します。現状は `AnyTaskNode` 型エイリアス 1 つだけを定義し、`TaskGraph` などの上位構造が「任意のノード」としてノードオブジェクトを参照できるようにします。

> ランタイムで使われる `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `TerminationSignal` / `CTreeEvent` / `ValueWrapper` などのコア型は本ファイルには含まれず、それぞれ `celestialflow.runtime` と `celestialflow.runtime.util_types` で提供されます。詳細は `docs/zh-CN/src/runtime/__init__.md` を参照。

## 公開型

### `AnyTaskNode`

```python
from typing import Any
from .core_node import BaseTaskNode

type AnyTaskNode = BaseTaskNode[Any, Any]
```

意味:

- 「任意入力 / 任意出力」に縮退した `BaseTaskNode`；
- 静的な型レベルでのみ使用され、ランタイムの動作には影響しない；
- 主に `TaskGraph` が管理する `node_dict` や、公共メソッド `connect` / `set_nodes` など「具体的な型を気にしない」位置で使われる。

## 典型的な使い方

```python
from celestialflow.node.util_types import AnyTaskNode


def collect_names(nodes: list[AnyTaskNode]) -> list[str]:
    return [n.get_name() for n in nodes]
```

> `AnyTaskNode` は単に型を消去するだけで、追加のランタイムオーバーヘッドは発生しません；呼び出し側は引き続き `isinstance(n, TaskExecutor | TaskSplitter | TaskRouter)` で細分化できます。

## 注意事項

1. **型エイリアスでありインポートリストには参加しない**：本ファイルには `__all__` がなく、`celestialflow.node.util_types` からの明示的な `import` は不要；`celestialflow.node` を経由して間接的にアクセスできます。
2. **範囲の限定**：`AnyTaskNode` を「具体的なノード」の位置に使うべきではありません。例えば `TaskExecutor[T, R]` の入力引数は引き続きジェネリックバージョンを使用し、静的推論を損なわないようにしてください。
3. **`runtime` モジュールの型との連携**：`BaseTaskNode` は内部で直接 `runtime` モジュールの `TaskEnvelope` / `TaskInQueue` / `TaskOutQueue` / `TaskMetrics` / `ValueWrapper` / `CTreeEvent` / `TerminationSignal` を使用しており、これらの型の詳細説明は対応するドキュメントを参照してください。
