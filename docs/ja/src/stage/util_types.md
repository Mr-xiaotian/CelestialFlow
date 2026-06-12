# StageTypes

> 📅 最終更新日: 2026/06/11

`stage/util_types.py` は Stage モジュールの型エイリアスを定義し、ジェネリック Stage への簡便な参照を提供します。

## コア型

### AnyTaskStage

`TaskStage` のジェネリックワイルドカードエイリアス。具体的な入出力型を指定する必要がない場合の型アノテーションに使用します。

```python
from typing import Any

from .core_stage import TaskStage

type AnyTaskStage = TaskStage[Any, Any]
```

| 属性 | 説明 |
|------|------|
| 正式名 | `TaskStage[Any, Any]` |
| 用途 | 型アノテーションにおけるワイルドカードプレースホルダー。具体的なデータ型を気にしないシナリオに適用 |
| 定義位置 | `stage/util_types.py`（`stage/core_stage.py` から `TaskStage` をインポート） |

## 使用例

### 型アノテーションでのワイルドカード使用法

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

# 任意の型の Stage を受け取れる変数を宣言する場合
def register_stage(stage: AnyTaskStage) -> None:
    print(f"Stage を登録しました: {stage.name}")

# 任意のジェネリックパラメータを持つ TaskStage を渡せる
int_stage: TaskStage[int, int] = TaskStage("A", func=lambda x: x * 2)
str_stage: TaskStage[str, str] = TaskStage("B", func=lambda x: x.upper())

register_stage(int_stage)  # 型チェックをパス
register_stage(str_stage)  # 型チェックをパス
```

### コンテナに複数型の Stage を格納

```python
from celestialflow.stage.util_types import AnyTaskStage
from celestialflow.stage import TaskStage

stages: list[AnyTaskStage] = []

stages.append(TaskStage("A", func=lambda x: x * 2))          # TaskStage[int, int]
stages.append(TaskStage("B", func=lambda x: x.upper()))      # TaskStage[str, str]
stages.append(TaskStage("C", func=lambda x: len(x)))         # TaskStage[str, int]

# 複雑なジェネリック型を手動でアノテーションする必要がない
for s in stages:
    print(f"  {s.name}: {s}")
```

## 注意事項

- `AnyTaskStage` は型アノテーションのみに使用され、実行時の動作は変更しません。実際の使用時には型チェッカー（Pyright / mypy など）が `TaskStage[Any, Any]` に展開します。
- この型エイリアスは Python 3.12+ の `type` ステートメント構文に依存します。
