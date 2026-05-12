# bench_graph_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/05/11

## 目標

異なる `stage_mode`（`serial` / `thread`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせにおける複雑な DAG のタスクグラフ実行性能を比較します。フレームワーク組み込みの `benchmark_graph` ツールを使用してマトリクス形式の比較を行います。

## テスト内容

### `bench_graph_0`
- **構造**：4 ノード DAG（`stage1 -> [stage2, stage3] -> stage4`）
- **タスク構成**：CPU 集約型（フィボナッチ）、I/O 集約型（sleep）、純粋な計算（半分、二乗）
- **入力**：`range(25, 32) + [0, 27, None, 0, ""]`（異常境界値を含む）
- **有効なサービス**：Reporter

### `bench_graph_1`
- **構造**：6 ノード多層 DAG（A -> [B, C] -> [D, E] -> F）
- **タスク**：ランダムな 0-2 秒スリープ（不均一な負荷のシミュレーション）
- **入力**：`range(10)`
- **有効なサービス**：Reporter

### `bench_graph_2`
- **構造**：4 ノード DAG（Splitter -> A -> [B, C]）、`TaskSplitter` で入力を展開
- **タスク**：純粋な計算（加算、乗算）、フレームワークのスケジューリングスループット上限をテスト
- **入力**：`range(10_000)`（Splitter により 10,000 個の独立タスクに展開）

## 主要設定

- `stage_modes = ["serial", "thread"]`
- `execution_sync_modes = ["serial", "thread"]`
- `execution_async_modes = ["async"]`
- 合計 **6 つの組み合わせ**で、それぞれグラフ全体を実行します
- `sync_graph`（同期関数）と `async_graph`（非同期関数）を別々に提供する必要があります

## 発生しうる問題

1. **環境変数の依存**：`REPORT_HOST` などは `.env` から読み込む必要があり、設定がない場合 reporter の接続が失敗します。
2. **合計所要時間が長い**：`benchmark_graph` は `len(stage_modes) x len(execution_modes)` 回の完全なグラフ実行を行います。I/O 遅延を含めると合計時間は数分に達する場合があります。

## 実行方法

```bash
python bench/bench_graph_mode.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、11 タスク（異常境界値を含む）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |

- CPU 集約型（フィボナッチ）シナリオでは、`thread` と `serial` の stage_mode の差はわずかです（GIL 制限）
- `execution_mode=thread` と `async` はともに 2-3x の高速化を提供します（フィボナッチ計算中の GIL 解放部分 + sleep ステージの I/O 並行性）
- `async` は `thread` と同程度の性能で、I/O 集約型シナリオでわずかに優位

### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |

- 最適な組み合わせ：`thread` + `async`（6.05s）、最悪の組み合わせ `serial`+`serial`（54.25s）より **9.0x** 高速
- `async` は I/O 集約型シナリオで `thread` より優れています（コルーチン切替オーバーヘッドがスレッド切替より小さい）
- `thread`（スレッドレイアウト）は I/O 集約型シナリオで `serial`（シングルスレッド逐次レイアウト）より大幅に優れ、各ステージを並列に起動できます

### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋な計算、10,000 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` が最速**（1.09s）：純粋な計算で I/O 待機なし、直接関数呼び出しのオーバーヘッドはゼロ
- `thread` は `serial` より 3.5x 遅い：マイクロ秒レベルのタスクではスレッドプール送信 + Future 同期のオーバーヘッドが増幅される
- `async` は `serial` より 10x 遅い：各タスクでコルーチンオブジェクトの作成 + イベントループスケジューリングが必要だが、並行性を活用できる I/O 待機ポイントがない
- `stage_mode=thread` もオーバーヘッドを増加：純粋な計算シナリオではステージ間のスレッドスケジューリングは純粋な負担
- **結論：純粋な計算集約型タスクには `serial` + `serial` を使用し、並行スケジューリングオーバーヘッドを回避すべき**

### まとめ

- `stage_mode=thread` は I/O 集約型シナリオで最適な選択です
- `execution_mode=async` は I/O 集約型シナリオで最高のパフォーマンスを発揮し、`thread` がそれに続き、`serial` が最も遅い
- **純粋な計算シナリオでは `serial` が最速**——`thread` と `async` のスケジューリングオーバーヘッドは I/O 待機なしでは償却できず、逆にボトルネックとなる
- `async` はステージの関数が async 関数である必要があるため、sync_graph と async_graph を別々に提供する必要があります
- 合計所要時間には、スレッド起動 + タスク実行 + キュー転送 + 終了シグナル伝播が含まれます

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部サービス：Reporter サービス（オプション）
