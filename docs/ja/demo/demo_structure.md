# demo_structure.py デモ説明

> 📅 最終更新日: 2026/05/24

## 目標

`core_structure.py` であらかじめ定義された複数のグラフ構造（DAG と循環グラフ）をデモし、CelestialFlow におけるチェーン、クロス、グリッド、ループ、ホイール、完全グラフなど多様なトポロジーでの構築と実行方法を示します。

## デモ構造

### DAG（有向非巡回グラフ）

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_chain` | TaskChain | 5 ノード線形チェーン、スレッドモード |
| `demo_forest` | TaskGraph | 2 つの独立したツリー状 DAG が共存 |
| `demo_cross` | TaskCross | 3 層クロス構造（3→1→3） |
| `demo_network` | TaskCross | 多層多分岐ネットワーク（2→3→1） |
| `demo_star` | TaskCross | 中心ノードが複数のエッジノードを指す |
| `demo_fanin` | TaskCross | 複数のソースノードが 1 つのマージノードに合流 |
| `demo_grid` | TaskGrid | 4×4 スレッドグリッド、staged スケジュール |

#### Chain（チェーン）— `demo_chain`

```mermaid
flowchart LR
    A["StageA<br/>square"] --> B["StageB<br/>square"]
    B --> C["StageC<br/>square"]
    C --> D["StageD<br/>square"]
    D --> E["StageE<br/>square"]
```

線形 5 ノードチェーン。データは `StageA → StageB → StageC → StageD → StageE` の順に流れ、各ノードは二乗演算を実行します。`TaskChain` で構築され、`start_chain()` で起動します。

#### Cross（クロス）— `demo_cross`

```mermaid
flowchart LR
    subgraph Layer1["第1層"]
        A["StageA"]
        B["StageB"]
        C["StageC"]
    end
    subgraph Layer2["第2層"]
        D["StageD"]
    end
    subgraph Layer3["第3層"]
        E["StageE"]
        F["StageF"]
        G["StageG"]
    end

    A --> D
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
```

3 層クロス構造（3→1→3）。`TaskCross` で構築され、`start_cross()` で起動します。

#### Network（ネットワーク）— `demo_network`

```mermaid
flowchart LR
    subgraph Input["入力層"]
        A1["A1"]
        A2["A2"]
    end
    subgraph Hidden["隠れ層"]
        B1["B1"]
        B2["B2"]
        B3["B3"]
    end
    subgraph Output["出力層"]
        C["C"]
    end

    A1 --> B1
    A1 --> B2
    A1 --> B3
    A2 --> B1
    A2 --> B2
    A2 --> B3
    B1 --> C
    B2 --> C
    B3 --> C
```

多層多分岐ネットワークトポロジー（2→3→1）。ニューラルネットワークのフォワード伝播構造をシミュレートします。

#### Star（スター）— `demo_star`

```mermaid
flowchart LR
    Core["Core<br/>square"] --> Side1["Side1<br/>add_5"]
    Core --> Side2["Side2<br/>add_10"]
    Core --> Side3["Side3<br/>add_15"]
```

中心ノード `Core` が計算結果を複数のエッジノードに配信し、各エッジノードが独立して処理します。

#### Fan-In（ファンイン）— `demo_fanin`

```mermaid
flowchart LR
    Source1["Source1<br/>add_5"] --> Merge["Merge<br/>add_one_sleep"]
    Source2["Source2<br/>add_10"] --> Merge
    Source3["Source3<br/>square"] --> Merge
```

複数のソースノード `Source1`、`Source2`、`Source3` の計算結果が 1 つのマージノード `Merge` に合流します。

#### Grid（グリッド）— `demo_grid`

```mermaid
flowchart TD
    Grid00["Grid00"] --> Grid01["Grid01"]
    Grid00 --> Grid10["Grid10"]
    Grid01 --> Grid02["Grid02"]
    Grid01 --> Grid11["Grid11"]
    Grid10 --> Grid11["Grid11"]
    Grid10 --> Grid20["Grid20"]
    Grid02 --> Grid03["Grid03"]
    Grid02 --> Grid12["Grid12"]
    Grid11 --> Grid12["Grid12"]
    Grid11 --> Grid21["Grid21"]
    Grid20 --> Grid21["Grid21"]
    Grid20 --> Grid30["Grid30"]
    Grid03 --> Grid13["Grid13"]
    Grid12 --> Grid13["Grid13"]
    Grid12 --> Grid22["Grid22"]
    Grid21 --> Grid22["Grid22"]
    Grid21 --> Grid31["Grid31"]
    Grid30 --> Grid31["Grid31"]
    Grid13 --> Grid23["Grid23"]
    Grid22 --> Grid23["Grid23"]
    Grid22 --> Grid32["Grid32"]
    Grid31 --> Grid32["Grid32"]
    Grid23 --> Grid33["Grid33"]
    Grid32 --> Grid33["Grid33"]
```

4×4 グリッドトポロジー。データは左上 `Grid00` から注入され、右下 `Grid33` へ層ごとに伝播します。

### 循環グラフ

| 関数 | 構造 | 説明 |
|------|------|------|
| `demo_loop` | TaskLoop | 3 ノード閉ループ、自己ロック構造 |
| `demo_wheel` | TaskWheel | 中心ノード + 4 つのループノード |
| `demo_complete` | TaskComplete | 3 ノード完全グラフ、全ペア接続 |
| `demo_multi_cycle` | TaskGraph | 多環相互接続グラフ：3 組の 2 ノード循環（A/B/C）、A2 から B1 と C1 に出力 |

#### Loop（ループ）— `demo_loop`

```mermaid
flowchart TD
    A["StageA<br/>add_one_sleep"] --> B["StageB<br/>add_one_sleep"]
    B --> C["StageC<br/>add_one_sleep"]
    C -.->|ループバック| A
```

3 ノード閉ループ自己ロック構造。`TaskLoop` で構築。タスクが入ると A → B → C → A の間を継続的に循環し、外部から終了されるまで続きます。

#### Wheel（ホイール）— `demo_wheel`

```mermaid
flowchart TD
    Core["Core<br/>square"] --> Side1["Side1<br/>add_one_sleep"]
    Core --> Side2["Side2<br/>add_one_sleep"]
    Core --> Side3["Side3<br/>add_one_sleep"]
    Core --> Side4["Side4<br/>add_one_sleep"]
    Side1 -.->|ループバック| Core
    Side2 -.->|ループバック| Core
    Side3 -.->|ループバック| Core
    Side4 -.->|ループバック| Core
```

ホイールトポロジー：中心 `Core` がタスクを 4 つのループノードに配信し、ループノードが処理完了後に `Core` にループバックし、継続的にローテーションします。`TaskWheel` で構築。

#### Complete（完全グラフ）— `demo_complete`

```mermaid
flowchart TD
    N1["Node1<br/>add_5"] <--> N2["Node2<br/>add_10"]
    N1 <--> N3["Node3<br/>square"]
    N2 <--> N3
```

3 ノード完全グラフ。すべてのノードが相互に接続されています。`TaskComplete` で構築され、データは全接続トポロジー内を流れます。

#### Multi-Cycle（多環相互接続）— `demo_multi_cycle`

```mermaid
flowchart TD
    subgraph CycleA["循環 A"]
        A1["A1"] --> A2["A2"]
        A2 -.->|ループバック| A1
    end

    subgraph CycleB["循環 B"]
        B1["B1"] --> B2["B2"]
        B2 -.->|ループバック| B1
    end

    subgraph CycleC["循環 C"]
        C1["C1"] --> C2["C2"]
        C2 -.->|ループバック| C1
    end

    A2 --> B1
    A2 --> C1
```

3 組の 2 ノード循環（A/B/C）。`A2` が `B1` と `C1` に出力し、多環相互接続を実現します。

### Forest（フォレスト）— `demo_forest`

```mermaid
flowchart TD
    subgraph Tree1["ツリー 1"]
        A["stageA"] --> C["stageC"]
        B["stageB"] --> D["stageD"]
        C --> E["stageE"]
        D --> E
    end

    subgraph Tree2["ツリー 2"]
        F["stageF"] --> G["stageG"]
        F --> H["stageH"]
        G --> I["stageI"]
        H --> J["stageJ"]
    end
```

2 つの独立したツリー状 DAG が同じ `TaskGraph` 内に共存し、互いに干渉しません。ツリー 1（A→C→E, B→D→E）とツリー 2（F→G→I, F→H→J）がそれぞれ独立して実行されます。

## 主要設定

- DAG 構造：`stage_mode="thread"`、`execution_mode="thread"`
- `demo_grid`：`staged` スケジュールモードを使用（層ごとに実行）
- 循環グラフ：`put_termination_signal=False`（外部制御での停止を推奨）
- すべてのデモで `Reporter` と `CelestialTree` を有効化

## 発生しうる問題

1. **循環グラフは自動停止しない**：`demo_loop`、`demo_complete` などは `put_termination_signal=False` を使用し、実行後は手動でプロセスを終了するまで継続的に循環します。
2. **sleep 遅延の蓄積**：`add_one_sleep` は 1 秒の sleep を含み、20 タスク × 多ノード = 長い総実行時間。
3. **アサーションなし**：フレームワークが起動・実行できることのみを検証し、結果の数値はチェックしません。

## 実行方法

```bash
python demo/demo_structure.py
```

## 想定される動作

実行後、各構造デモが順に実行され、各 Stage の入出力ログと最終サマリーが出力されます。

### DAG 構造

```
=== demo_chain (5-node linear chain) ===
[StageA] Input: 2 -> Output: 4
[StageB] Input: 4 -> Output: 16
[StageC] Input: 16 -> Output: 256
[StageD] Input: 256 -> Output: 65536
[StageE] Input: 65536 -> Output: 4294967296
```

```
=== demo_grid (4x4 grid, staged scheduling) ===
[Grid00] -> [Grid01] [Grid10]
[Grid01] -> [Grid02] [Grid11]
...
--- Summary ---
Grid00: success=5  fail=0
Grid33: success=5  fail=0
```

### 循環グラフ

```
=== demo_loop (3-node closed loop) ===
[StageA] Input: 1 -> Output: 2
[StageB] Input: 2 -> Output: 3
[StageC] Input: 3 -> Output: 4
[StageA] Input: 4 -> Output: 5
... (継続的に循環、自動停止しません)
```

```
=== demo_complete (3-node complete graph) ===
[Node1] Input: 5 -> Output: 10
[Node2] Input: 10 -> Output: 20
[Node3] Input: 20 -> Output: 400
... (継続的に循環)
```

> **重要**：`demo_loop`、`demo_wheel`、`demo_complete` などの循環グラフは `put_termination_signal=False` を使用し、実行後は自動停止しません。**Ctrl+C** で手動終了してください。

### Forest（フォレスト）

2 つの独立した DAG がそれぞれ実行され、互いに干渉しません：

```
=== demo_forest (disjoint DAGs) ===
[stageA] Input: 1 -> Result: 2
[stageB] Input: 2 -> Result: 3
[stageF] Input: 3 -> Result: 4
[stageC] Input: ...
```

> 各構造の実行前に `=== demo_xxx ===` の区切り線が表示され、`Summary` セクションに各ノードの成功/失敗カウントが表示されます。

## 依存

- `celestialflow`（`TaskGraph`、`TaskChain`、`TaskCross`、`TaskGrid`、`TaskLoop`、`TaskWheel`、`TaskComplete`、`TaskStage`）
- `demo_utils`
- `python-dotenv`
- 外部サービス：CelestialTree（オプション）、Reporter（オプション）
