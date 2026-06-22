# bench_graph_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/06/22

## 目的

異なる `stage_mode`（`serial` / `thread`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせにおいて、複雑な DAG タスクグラフの実行性能を比較する。フレームワーク内蔵の `benchmark_graph` ツールを使用し、マトリックス形式で比較する。

## テスト内容

### `bench_graph_0`
- **構造**：4 ノード DAG。`stage1 → stage2 → stage4`、`stage1 → stage3`（stage3 は stage4 に合流しない独立したブランチ）
- **タスク混合**：CPU 集約型（フィボナッチ）、I/O 集約型（sleep）、純粋計算（2 で割る、2 乗）
- **入力**：`range(25, 32) + [0, 27, None, 0, ""]`（異常境界を含む）
- **リトライ設定**：`stage1`、`stage2` で `ValueError` に対し `max_retries=1` を有効化
- **有効サービス**：Reporter

### `bench_graph_1`
- **構造**：6 ノード多層 DAG（`A → [B, C]`、`B → [D, E]`、`C → E`、`D → F`）
- **タスク**：ランダム 0-2 秒 sleep（不均一負荷のシミュレーション）
- **入力**：`range(10)`
- **有効サービス**：Reporter

### `bench_graph_2`
- **構造**：4 ノード DAG（Splitter → A → [B, C]）。`TaskSplitter` で入力を展開
- **タスク**：純粋計算（+1、×2）。フレームワークのスケジューリングスループット上限をテスト
- **入力**：`range(10_000)`（Splitter により 10,000 個の独立タスクに展開）

## 主要設定

- `benchmark_graph` は内部で `stage_mode`（`serial` / `thread`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせを走査し、合計 **6 種類の組み合わせ**でグラフを完全実行する
- 本ファイルはこれらのモードを直接設定せず、同期 `TaskGraph` オブジェクトと非同期 `TaskGraph` オブジェクトを `benchmark_graph` に渡すだけである

## 発生し得る問題

1. **環境変数依存**：`REPORT_HOST` 等は `.env` から読み込む必要があり、未設定の場合は reporter 接続に失敗する。
2. **合計所要時間が長い**：`benchmark_graph` は `len(stage_modes) × len(execution_modes)` 回の完全なグラフ実行を行い、I/O 遅延を含む場合の合計時間は数分に達する可能性がある。

## 実行方法

```bash
python bench/bench_graph_mode.py
```

## パラメータ調整

### 特定テストシナリオの単独実行

`bench/bench_graph_mode.py` の `main()` で特定のシナリオのみを実行できる：

```python
if __name__ == "__main__":
    bench_graph_0()     # 运行 4 节点 DAG 混合场景（默认已注释）
    bench_graph_1()     # 当前启用：6 节点多层 DAG
    bench_graph_2()     # 当前启用：Splitter 吞吐量测试
```

### 入力規模の調整

```python
# bench_graph_2 默认输入 range(10_000)，可减小以快速验证
# 在函数内部修改输入范围
inputs = range(1_000)  # 改为 1000 个任务，快速验证
```

### ワーカー数の変更

各シナリオのデフォルトワーカー数はコード内で直接調整可能：

```python
# 在 bench_graph_0 内部
max_workers = 4   # 减少并发 Worker
```

修正後に実行：

```bash
python bench/bench_graph_mode.py
```

## ベンチマーク結果（実測）

### 履歴結果 - Windows グラフモード比較（日時未記録）

> 環境：Windows、Python 3.10

#### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、11 タスク（異常境界を含む）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.74s | 2.76s | 2.74s |
| **thread** | 7.19s | 2.28s | 2.14s |
| **process** | 9.88s | 4.99s | - |

注: `process` モードは廃止済み、bench データのみ保持

- `thread` と `serial` の stage_mode は CPU 集約型（フィボナッチ）シナリオで大きな差はない（GIL 制限）
- `execution_mode=thread` と `async` はいずれも 2-3x の高速化（フィボナッチ計算で GIL が解放される部分 + sleep フェーズの I/O 並行性）
- `async` と `thread` の性能は近く、async は I/O 集約型シナリオでわずかに優位

#### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 54.25s | 17.12s | 14.14s |
| **thread** | 17.10s | 7.07s | 6.05s |
| **process** | 20.47s | 10.98s | - |

注: `process` モードは廃止済み、bench データのみ保持

- 最適組み合わせ：`thread` + `async`（6.05s）。最悪組み合わせ `serial`+`serial`（54.25s）比で **9.0x** 高速
- `async` は I/O 集約型シナリオで `thread` より優位（コルーチン切り替えのオーバーヘッドがスレッド切り替えより小さい）
- `thread`（スレッドレイアウト）は I/O 集約型シナリオで `serial`（シングルスレッド直列レイアウト）より顕著に優位。各 stage を並列起動可能

#### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋計算、10,000 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.09s | 3.89s | 10.73s |
| **thread** | 2.79s | 5.30s | 11.40s |

- **`serial` + `serial` が最速**（1.09s）：純粋計算で I/O 待機なし。直接関数呼び出しでオーバーヘッドゼロ
- `thread` は `serial` より 3.5x 遅い：スレッドプール送信 + Future 同期のオーバーヘッドがマイクロ秒レベルのタスクで増幅
- `async` は `serial` より 10x 遅い：各タスクがコルーチンオブジェクト作成 + イベントループスケジューリングを必要とするが、並行性を活用できる I/O 待機ポイントがない
- `stage_mode=thread` もオーバーヘッドを追加：stage 間のスレッドスケジューリングが純粋計算シナリオでは純粋な負担
- **結論：純粋計算集約型タスクには `serial` + `serial` を使用し、並行スケジューリングオーバーヘッドを回避すべき**

#### 総括

- `stage_mode=thread` は I/O 集約型シナリオで最適
- `execution_mode=async` は I/O 集約型シナリオで最高のパフォーマンス、`thread` が次点、`serial` が最も遅い
- **純粋計算シナリオでは `serial` が最速** — `thread` と `async` のスケジューリングオーバーヘッドは I/O 待機がない場合に償却されず、むしろボトルネックとなる
- `async` には stage の関数が async 関数である必要があるため、`sync_graph` と `async_graph` を別々に提供する必要がある
- 合計所要時間に含まれるもの：スレッド起動 + タスク実行 + キュー転送 + 終了シグナル伝播

### 2026/06/16 - 今回の再実行試行（未安定完了）

> 環境：Windows、Reporter サービスの向き先 `127.0.0.1:5005`

- 今回、現在のスクリプトエントリに従って `bench_graph_mode.py` の再実行を試行した
- コマンドは現在の環境で長時間にわたり安定した完全な所要時間表を返さず、一時ログは単一行のヘッダーのみに留まった
- 不完全なデータを正式な benchmark 記録として記載することを避けるため、今回は新しい所要時間表を追加せず、履歴結果を引き続き参考として保持

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部サービス：Reporter サービス（オプション）
