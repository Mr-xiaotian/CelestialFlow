# bench_graph_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/05/15

## 目的

複雑な DAG に対して、`stage_mode`（`serial` / `thread`）と `execution_mode`（`serial` / `thread` / `async`）の異なる組み合わせでのタスクグラフ実行性能を比較する。フレームワーク内蔵の `benchmark_graph` ツールを使用してマトリクス形式の比較を行う。

## テスト内容

### `bench_graph_0`
- **構造**：4 ノード DAG（`stage1 → [stage2, stage3] → stage4`）
- **タスク混合**：CPU 集約型（フィボナッチ）、I/O 集約型（sleep）、純粋計算（半分、二乗）
- **入力**：`range(25, 32) + [0, 27, None, 0, ""]`（エッジケース含む）
- **有効サービス**：Reporter

### `bench_graph_1`
- **構造**：6 ノード多層 DAG（A → [B, C] → [D, E] → F）
- **タスク**：ランダム 0-2 秒スリープ（不均一な負荷のシミュレーション）
- **入力**：`range(10)`
- **有効サービス**：Reporter

### `bench_graph_2`
- **構造**：4 ノード DAG（Splitter → A → [B, C]）、`TaskSplitter` で入力を展開
- **タスク**：純粋計算（1 加算、2 倍）、フレームワークのスケジューリングスループット上限をテスト
- **入力**：`range(10_000)`（Splitter により 10,000 個の独立タスクに展開）

## 主要設定

- `benchmark_graph` は内部で `stage_mode`（`serial` / `thread`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせを反復し、合計 **6 種類の組み合わせ**でそれぞれ完全なグラフを実行する
- 本ファイルはこれらのモードを直接設定せず、`sync_graph`（同期関数）と `async_graph`（非同期関数）を `benchmark_graph` に渡すのみ

## 発生し得る問題

1. **環境変数の依存**：`REPORT_HOST` 等は `.env` から読み込む必要があり、未設定の場合 reporter の接続に失敗する。
2. **合計実行時間が長い**：`benchmark_graph` は `len(stage_modes) × len(execution_modes)` 回の完全なグラフ実行を行い、I/O 遅延を含めると数分かかる場合がある。

## 実行方法

```bash
python bench/bench_graph_mode.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、11 タスク（エッジケース含む）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |

- `thread` と `serial` の stage_mode は CPU 集約型（フィボナッチ）シナリオでほとんど差がない（GIL の制約）
- `execution_mode=thread` と `async` はいずれも 2-3 倍の高速化を実現（フィボナッチ計算での部分的な GIL 解放 + sleep ステージでの I/O 並行処理）
- `async` と `thread` の性能は近接しており、I/O 集約型シナリオでは async がわずかに優位

### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |

- 最適な組み合わせ：`thread` + `async`（6.05s）、最悪の組み合わせ `serial`+`serial`（54.25s）の **9.0 倍**高速
- `async` は I/O 集約型シナリオで `thread` を上回る（コルーチン切り替えのオーバーヘッドがスレッド切り替えより小さい）
- `thread`（スレッドレイアウト）は I/O 集約型シナリオで `serial`（シングルスレッド逐次レイアウト）を大幅に上回る。各 stage が並列に開始可能

### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋計算、10,000 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` が最速**（1.09s）：I/O 待機のない純粋計算、直接関数呼び出しでオーバーヘッドゼロ
- `thread` は `serial` より 3.5 倍遅い：スレッドプール送信 + Future 同期のオーバーヘッドがマイクロ秒レベルのタスクで増幅
- `async` は `serial` より 10 倍遅い：各タスクでコルーチンオブジェクトの生成 + イベントループスケジューリングが発生するが、並行処理を活用できる I/O 待機ポイントがない
- `stage_mode=thread` もオーバーヘッドを追加：stage 間のスレッドスケジューリングは純粋計算シナリオでは純粋な負担
- **結論：純粋な計算集約型タスクでは並行スケジューリングオーバーヘッドを避けるため `serial` + `serial` を使用すべき**

### まとめ

- `stage_mode=thread` は I/O 集約型シナリオでの最適な選択
- `execution_mode=async` は I/O 集約型シナリオで最良、次いで `thread`、`serial` が最も遅い
- **純粋計算シナリオでは `serial` が最速** — I/O 待機がない場合、`thread` と `async` のスケジューリングオーバーヘッドは償却されず、かえってボトルネックになる
- `async` は stage の関数が async 関数である必要があるため、sync_graph と async_graph を別々に提供する必要がある
- 合計所要時間にはスレッド起動 + タスク実行 + キュー転送 + 終了シグナル伝播が含まれる

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部サービス：Reporter サービス（オプション）
