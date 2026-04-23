# bench_graph.py ベンチマーク説明

> 📅 最終更新日: 2026/04/22

## 目標

異なる `stage_mode`（`serial` / `thread` / `process`）と `execution_mode`（`serial` / `thread`）の組み合わせにおける複雑な DAG のタスクグラフ実行性能を比較します。フレームワーク組み込みの `benchmark_graph` ツールを使用してマトリクス形式の比較を行います。

## テスト内容

### `bench_graph_0`
- **構造**：4 ノード DAG（`stage1 -> [stage2, stage3] -> stage4`）
- **タスク構成**：CPU 集約型（フィボナッチ）、I/O 集約型（sleep）、純粋な計算（半分、二乗）
- **入力**：`range(25, 32) + [0, 27, None, 0, ""]`（異常境界値を含む）
- **有効なサービス**：Reporter、CelestialTree

### `bench_graph_1`
- **構造**：6 ノード多層 DAG（A -> [B, C] -> [D, E] -> F）
- **タスク**：ランダムな 0-2 秒スリープ（不均一な負荷のシミュレーション）
- **入力**：`range(10)`
- **有効なサービス**：Reporter、CelestialTree

## 主要設定

- `stage_modes = ["serial", "thread", "process"]`
- `execution_modes = ["serial", "thread"]`
- 合計 **6 つの組み合わせ**で、それぞれグラフ全体を実行します

## 発生しうる問題

1. **環境変数の依存**：`REPORT_HOST`、`CTREE_HOST` などは `.env` から読み込む必要があり、設定がない場合 reporter/ctree の接続が失敗します。
2. **CelestialTree 未起動**：`set_ctree(True)` を設定してもサービスが稼働していない場合、`start_graph()` が接続例外をスローします。
3. **Windows マルチプロセスオーバーヘッド**：`stage_mode="process"` では各ステージが独立プロセスを起動します。4 ステージの DAG では Windows 上のプロセス起動時間が実際のタスク実行時間を超える場合があります。
4. **合計所要時間が長い**：`benchmark_graph` は `len(stage_modes) x len(execution_modes)` 回の完全なグラフ実行を行います。I/O 遅延を含めると合計時間は数分に達する場合があります。

## 実行方法

```bash
python bench/bench_graph.py
```

## ベンチマーク結果（実測）

> 環境：Windows、Python 3.10

### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、11 タスク（異常境界値を含む）

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 7.70s | 2.82s |
| **thread** | 7.12s | 2.63s |
| **process** | 9.88s | 4.99s |

- CPU 集約型（フィボナッチ）シナリオでは、`thread` と `serial` の stage_mode の差はわずかです（GIL 制限）
- `process` はプロセス起動オーバーヘッドにより最も遅い結果となりました
- `execution_mode=thread` は依然として 2-3x の高速化を提供します（フィボナッチ計算中の GIL 解放部分 + sleep ステージの I/O 並行性）

### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| stage_mode \ execution_mode | serial | thread |
|----------------------------|--------|--------|
| **serial** | 61.20s | 17.08s |
| **thread** | 17.07s | 7.07s |
| **process** | 20.47s | 10.98s |

- 最適な組み合わせ：`thread` + `thread`（7.07s）、最悪の組み合わせ `serial`+`serial`（61.20s）より **8.7x** 高速
- `thread`（スレッドレイアウト）は I/O 集約型シナリオで `process`（マルチプロセスレイアウト）より優れ、プロセス起動とプロセス間シリアライゼーションのオーバーヘッドを節約します
- `process`（マルチプロセスレイアウト）は依然として `serial`（シングルプロセス逐次レイアウト）より大幅に優れ、各ステージを並列に起動できます

### まとめ

- `stage_mode=thread` は I/O 集約型シナリオで最適な選択であり、lambda 関数などの pickle 不可能なオブジェクトもサポートします
- `stage_mode=process` は GIL を回避する必要がある CPU 集約型シナリオに適していますが、Windows ではプロセス起動オーバーヘッドが大きくなります
- `execution_mode=thread` はすべてのシナリオで `serial` より優れています
- 合計所要時間には、プロセス/スレッド起動 + タスク実行 + キュー転送 + 終了シグナル伝播が含まれます

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部サービス：CelestialTree（オプション）、Reporter サービス（オプション）
