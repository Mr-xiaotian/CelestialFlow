# TaskStages

> 📅 最終更新日: 2026/08/26

`stage/core_stages.py` は 2 種類の内蔵構造型 `TaskStage` 特殊化を提供します：`TaskSplitter`（スプリッター）と `TaskRouter`（ルーター）です。これらはグラフ構造と下流分配セマンティクスを変更するもので、一般的なパイプライン編成シナリオ向けです。

## TaskSplitter (スプリッター)

```mermaid
flowchart LR
    subgraph TG[TaskSplitter]
        direction LR

        T1[Last Stage]
        T2[Next Stage]

        TS[[TaskSplitter]]

        T1 -->|1 task| TS
        TS -->|N task| T2

    end

    %% 美化 TaskGraph 外枠
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 統一美化フォーマット
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2 blueNode;

    %% 美化 特殊Stage
    class TS blueNode;

```

単一の入力タスクを複数の出力タスクに分割します。一対多のシナリオに適しています。

### 初期化

```python
class TaskSplitter[TItem, RItem](TaskStage[Iterable[TItem], Iterable[RItem]]):
    def __init__(
        self,
        name: str,
        split_item: Callable[[TItem], RItem] | None = None,
    ):
        """
        TaskSplitter を初期化します。

        :param name: ノード名
        :param split_item: カスタム単一サブタスク処理関数。デフォルトは恒等写像を使用
        """
```

### 使用方法

```python
class MySplitter(TaskSplitter):
    def _split(self, task):
        # 入力データを複数の部分に分割
        return tuple(task)


splitter = MySplitter("MySplitter")
```

### 特性

- **メカニズム**: 1 つのタスクを入力とし、`_split` が返すタプルの各要素が独立した `TaskEnvelope` にラップされて下流に送信されます。
- **カウント**: 内部で `split_counter` を保持し、分割された総タスク数を統計します。
- **固定設定**: `execution_mode="serial"`, `max_retries=0`（`__init__` 内でハードコード）。
- **split_item**: オプションのカスタムサブタスク処理関数。各分割項目に対して前処理を行います。

---

## TaskRouter (ルーター)

```mermaid
flowchart LR
    subgraph TG[TaskRouter]
        direction LR

        T1[Last Stage]
        T2[Next Stage 1]
        T3[Next Stage 2]

        TR{{TaskRouter}}

        T1 -->|2 task| TR
        TR -->|1 task| T2
        TR -->|1 task| T3

    end

    %% 美化 TaskGraph 外枠
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px

    %% 統一美化フォーマット
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;

    %% 美化 TaskStages
    class T1,T2,T3 blueNode;

    %% 美化 特殊Stage
    class TR blueNode;

```

条件に応じてタスクを異なる下流パスに振り分けます。

### 初期化

```python
class TaskRouter[T](TaskStage[T, tuple[str, T]]):
    def __init__(self, name: str, router: Callable[[T], str]):
        """
        TaskRouter を初期化します。

        :param name: ノード名
        :param router: ルーティング関数。タスクデータに応じてターゲット stage 名を返す
        """
```

### 使用方法

`TaskRouter` は上流が事前に `(target_tag, data)` タプルを構築する必要がなくなり、自身が保持する `router(task) -> str` 関数が下流の決定を担当します：

```python
# ルーティング関数を定義：タスク内容に応じて下流ノード名を返す
def route_logic(data: int) -> str:
    if data > 0:
        return "positive_stage"
    else:
        return "negative_stage"


# 上流は元のタスクのみを生成
source = TaskStage("Source", func=lambda x: x)

# Router が内部でルーティング決定
router = TaskRouter("Router", route_logic)

# 下流を接続（戻り値は下流 stage 名と一致しなければならない）
pos_stage = TaskStage("positive_stage", func=lambda x: x)
neg_stage = TaskStage("negative_stage", func=lambda x: x)

graph = TaskGraph("RouterGuide")
graph.set_stages([source, router, pos_stage, neg_stage])
graph.connect([source], [router])
graph.connect([router], [pos_stage, neg_stage])
```

### 特性

- **メカニズム**: 元のタスク `task` を受信し、まず `router(task)` を呼び出してターゲット名を計算し、次に元の `task` を対応する下流 Stage に送信します。
- **カウント**: 各ターゲットに対して独立したカウンター `route_counters` を保持。
- **エラー処理**: `router(task)` が返すターゲット名がバインド済みの下流リストに存在しない場合、`InvalidOptionError` が送出されます。
- **固定設定**: `execution_mode="serial"`, `max_retries=0`（`__init__` 内でハードコード）。

---

## 使用例

### TaskSplitter：1 件のレコードを複数に分割

```python
from celestialflow import TaskGraph, TaskStage, TaskSplitter


# カスタムスプリッター：テキストを行で分割
class LineSplitter(TaskSplitter):
    def _split(self, task):
        return tuple(task.split("\n"))


# 後続処理ステージを定義
source = TaskStage("Input", func=lambda x: x)
splitter = LineSplitter("SplitLines")
processor = TaskStage("Process", func=lambda x: f">>> {x}")

graph = TaskGraph()
graph.set_stages([source, splitter, processor])
graph.connect([source], [splitter])
graph.connect([splitter], [processor])

# 3 行を含むテキストを入力し、3 つの独立タスクに分割
text_data = "line1\nline2\nline3"
graph.run({source.get_name(): [text_data]})
```

### TaskRouter：条件に応じたタスク振り分け

```python
from celestialflow import TaskGraph, TaskStage, TaskRouter


# ルーティング判定ロジックを定義（ターゲット名のみを返す）
def classify_number(x: int) -> str:
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"


# グラフノードを構築
source = TaskStage("Source", func=lambda x: x)
router = TaskRouter("Router", classify_number)
handler_pos = TaskStage("positive", func=lambda x: f"Positive: {x}")
handler_neg = TaskStage("negative", func=lambda x: f"Negative: {x}")
handler_zero = TaskStage("zero", func=lambda x: f"Zero: {x}")

graph = TaskGraph("RouterDemo")
graph.set_stages([source, router, handler_pos, handler_neg, handler_zero])
graph.connect([source], [router])
graph.connect([router], [handler_pos, handler_neg, handler_zero])

graph.run({source.get_name(): [10, -5, 0, 3, -1]})
```

> **注意**: `router(task)` の戻り値は下流 `TaskStage` の `name` と完全一致する必要があります。

---

## 注意事項

1. **構造型ノードの位置づけ**: `TaskSplitter` と `TaskRouter` はグラフ構造と下流分配セマンティクスを変更するものであり、フレームワーク内蔵ノードとして保持するのに適しています。
2. **カスタムプロトコル実装**: Redis、メッセージキュー、RPC などの外部システムとの連携は、呼び出し側が通常の `TaskStage` で独自に実装する方が適しています。
