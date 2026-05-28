# TaskStructure

> 📅 最終更新日: 2026/05/28

TaskStructure モジュールは、ユーザーが複雑なタスクフローを素早く構築できるよう、さまざまな定義済みタスクグラフ構造を提供します。すべての構造は `TaskGraph` を継承しています。

## Chain（線形チェーン）

```mermaid
flowchart LR
    subgraph TC[TaskChain]
        direction LR
        S1[Stage 1]
        S2[Stage 2]
        S3[Stage 3]
        S1 --> S2 --> S3
    end
    style TC fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S1,S2,S3 blueNode;
```

`TaskChain` は最もシンプルなタスク構造で、複数の `TaskStage` を順番に接続し、線形のデータフローを形成します。

```python
from celestialflow import TaskChain, TaskStage

# ステージの定義
stage1 = TaskStage("S1", func=func1)
stage2 = TaskStage("S2", func=func2)
stage3 = TaskStage("S3", func=func3)

# チェーンの作成
chain = TaskChain(
    stages=[stage1, stage2, stage3],
    stage_mode="thread",  # thread: ノード並行実行; serial: ノード順次実行
    log_level="SUCCESS"
)

# 開始
chain.start_chain(init_tasks_dict={stage1.get_name(): [data]})
```

## Cross（クロスレイヤー）

```mermaid
flowchart LR
    subgraph TC[TaskCross]
        direction LR
        
        S11[Stage 1-1]
        S12[Stage 1-2]
        
        S21[Stage 2-1]
        S22[Stage 2-2]

        S11 --> S21
        S11 --> S22
        S12 --> S21
        S12 --> S22
    end
    style TC fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S11,S12,S21,S22 blueNode;
```

`TaskCross` はタスクを「レイヤー」で組織します。各レイヤーには並列実行される複数のノードが含まれます。隣接するレイヤー間のノードは全結合の依存関係を持ちます（前のレイヤーの各ノードが次のレイヤーのすべてのノードに接続）。

```python
from celestialflow import TaskCross

# レイヤーの定義
layer1 = [stage_1_1, stage_1_2]
layer2 = [stage_2_1, stage_2_2]

# クロス構造の作成
cross = TaskCross(
    layers=[layer1, layer2],
    schedule_mode="eager"
)
```

## Grid（グリッド）

```mermaid
flowchart TD
    subgraph TG[TaskGrid]
        direction TB
        S00[Stage 0,0]
        S01[Stage 0,1]
        S10[Stage 1,0]
        S11[Stage 1,1]

        S00 --> S01
        S00 --> S10
        S01 --> S11
        S10 --> S11
    end
    style TG fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S00,S01,S10,S11 blueNode;
```

`TaskGrid` はタスクノードを二次元グリッドに組織します。各ノードは**右側**と**下方**のノードに接続します。

```python
from celestialflow import TaskGrid

# グリッドの定義
grid_layout = [
    [stage_00, stage_01],
    [stage_10, stage_11]
]

# グリッド構造の作成
grid = TaskGrid(
    grid=grid_layout,
    schedule_mode="eager"
)
```

## Loop（リング）

```mermaid
flowchart LR
    subgraph TL[TaskLoop]
        direction LR
        S1[Stage 1]
        S2[Stage 2]
        S3[Stage 3]
        
        S1 --> S2 --> S3 --> S1
    end
    style TL fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S1,S2,S3 blueNode;
```

`TaskLoop` はノードを首尾接続して閉ループを形成します。循環の特性上、`eager` スケジューリングモードが強制されます。
注意：ループ構造は通常、外部からの介入による停止、または特定の終了条件の設定が必要です。

```python
from celestialflow import TaskLoop

# ループの作成
loop = TaskLoop(
    stages=[stage1, stage2, stage3]  # stage3 -> stage1
)
```

## Wheel（ホイール）

```mermaid
flowchart TD
    subgraph TW[TaskWheel]
        direction TB
        C((Center))
        R1[Ring 1]
        R2[Ring 2]
        R3[Ring 3]
        
        C --> R1
        C --> R2
        C --> R3
        
        R1 --> R2 --> R3 --> R1
    end
    style TW fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class C,R1,R2,R3 blueNode;
```

`TaskWheel` は中心ノードとリング構造を含みます。中心ノードはリング上のすべてのノードに接続し、リング上のノードは首尾接続されます。

```python
from celestialflow import TaskWheel

# ホイール構造の作成
wheel = TaskWheel(
    center=center_stage,
    ring=[ring_stage1, ring_stage2, ring_stage3]
)
```

## Complete（完全グラフ）

```mermaid
flowchart LR
    subgraph TC[TaskComplete]
        direction LR
        S1[Stage 1]
        S2[Stage 2]
        S3[Stage 3]
        
        S1 <--> S2
        S2 <--> S3
        S3 <--> S1
    end
    style TC fill:#e8f2ff,stroke:#6b93d6,stroke-width:2px,color:#0b1e3f,rx:10px,ry:10px
    classDef blueNode fill:#ffffff,stroke:#6b93d6,rx:6px,ry:6px;
    class S1,S2,S3 blueNode;
```

`TaskComplete` は特殊な構造で、各ノードが自分自身を除くすべてのノードに接続します。

```python
from celestialflow import TaskComplete

# 完全グラフの作成
complete = TaskComplete(
    stages=[stage1, stage2, stage3, stage4]
)
```

## 使用例

以下に、各定義済みグラフ構造の具体的な構築と実行方法を示します。

### TaskChain 完全な例

```python
from celestialflow import TaskChain, TaskStage

# 3つのステージを定義：データクリーニング → 変換 → 集計
def clean(data: str) -> str:
    return data.strip()

def transform(data: str) -> int:
    return int(data) * 2

def aggregate(data: int) -> dict:
    return {"original": data // 2, "doubled": data}

# チェーンを構築
s1 = TaskStage("Clean", func=clean)
s2 = TaskStage("Transform", func=transform)
s3 = TaskStage("Aggregate", func=aggregate)
chain = TaskChain(stages=[s1, s2, s3], stage_mode="thread")

# 開始
chain.start_chain({s1.get_name(): [" 10 ", " 20 ", " 30 "]})

# 結果を取得
print(f"チェーンサマリー: {chain.get_graph_summary()}")
```

### TaskCross 完全な例

```python
from celestialflow import TaskCross, TaskStage

# レイヤー1：データ準備
def load_a(x: int) -> int:
    return x + 1

def load_b(x: int) -> int:
    return x * 10

# レイヤー2：計算分析
def analyze_a(x: int) -> float:
    return x * 1.5

def analyze_b(x: int) -> float:
    return x * 2.0

layer1 = [TaskStage("LoadA", func=load_a), TaskStage("LoadB", func=load_b)]
layer2 = [TaskStage("AnaA", func=analyze_a), TaskStage("AnaB", func=analyze_b)]

cross = TaskCross(layers=[layer1, layer2])
cross.start_cross({layer1[0].get_name(): [1, 2], layer1[1].get_name(): [3, 4]})
print(cross.get_graph_summary())
```

### TaskGrid 完全な例

```python
from celestialflow import TaskGrid, TaskStage

# 2x2 グリッド
n00 = TaskStage("Init", func=lambda x: x)
n01 = TaskStage("Add", func=lambda x: x + 1)
n10 = TaskStage("Mul", func=lambda x: x * 2)
n11 = TaskStage("Square", func=lambda x: x * x)

grid = TaskGrid(grid=[[n00, n01], [n10, n11]])
grid.start_grid({n00.get_name(): [1, 2, 3]})
print(grid.get_graph_summary())
```

### TaskLoop 完全な例

```python
from celestialflow import TaskLoop, TaskStage

# 3ノードリング：各ノードが処理して結果を次に渡す
loop_stages = [
    TaskStage("Ring1", func=lambda x: x + 1),
    TaskStage("Ring2", func=lambda x: x * 2),
    TaskStage("Ring3", func=lambda x: x - 3),  # Ring3 -> Ring1 が閉ループを形成
]

loop = TaskLoop(loop_stages)
loop.start_loop(
    {loop_stages[0].get_name(): [5]},
    put_termination_signal=False,  # リング構造は手動での終了注入が必要
)
```

### TaskWheel 完全な例

```python
from celestialflow import TaskWheel, TaskStage

center = TaskStage("Hub", func=lambda x: {"input": x, "processed": x * 10})
ring_nodes = [
    TaskStage("Channel1", func=lambda x: x["processed"] + 1),
    TaskStage("Channel2", func=lambda x: x["processed"] + 2),
    TaskStage("Channel3", func=lambda x: x["processed"] + 3),
]

wheel = TaskWheel(center=center, ring=ring_nodes)
wheel.start_wheel({center.get_name(): [42]})
print(wheel.get_graph_summary())
```

### TaskComplete 完全な例

```python
from celestialflow import TaskComplete, TaskStage

nodes = [
    TaskStage("N1", func=lambda x: x ** 2),
    TaskStage("N2", func=lambda x: x + 1),
    TaskStage("N3", func=lambda x: x // 2),
]

complete = TaskComplete(nodes)
complete.start_complete(
    {nodes[0].get_name(): [10]},
    put_termination_signal=False,
)
print(complete.get_graph_summary())
```
