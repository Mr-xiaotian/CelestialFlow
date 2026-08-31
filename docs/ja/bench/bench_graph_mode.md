# bench_graph_mode.py ベンチマーク説明

> 📅 最終更新日: 2026/08/31

## 目的

異なる `graph_mode`（`serial` / `thread` / `async`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせにおいて、複雑な DAG のタスクグラフ実行性能を比較する。フレームワーク内蔵の `benchmark_graph` ツールを使用し、3×3 マトリックス形式で比較する。

## テスト内容

### `bench_graph_0`
- **構造**：4 ノード DAG。`stage1 → stage2 → stage4`、`stage1 → stage3`（stage3 は stage4 に合流しない独立したブランチ）
- **タスク混合**：CPU 集約型（フィボナッチ）、I/O 集約型（sleep）、純粋計算（2 で割る、2 乗）
- **入力**：`range(25, 32)`（7 個の純粋な成功タスク。早期バージョンには異常入力が含まれていたが、削除済み）
- **リトライ設定**：`stage1`、`stage2` で `ValueError` に対し `max_retries=1` を有効化（現在の入力では発火しない）
- **Reporter**：デフォルトで無効（コード内でコメントアウト済み。コメント解除で有効化可能）

### `bench_graph_1`
- **構造**：6 ノード多層 DAG（`A → [B, C]`、`B → [D, E]`、`C → E`、`D → F`）
- **タスク**：ランダム 0-2 秒 sleep（不均一負荷のシミュレーション）
- **入力**：`range(10)`
- **Reporter**：デフォルトで無効（コード内でコメントアウト済み。コメント解除で有効化可能）

### `bench_graph_2`
- **構造**：4 ノード DAG（Splitter → A → [B, C]）。`TaskSplitter` で入力を展開
- **タスク**：純粋計算（+1、×2）。フレームワークのスケジューリングスループット上限をテスト
- **入力**：`range(10_000)`（Splitter により 10,000 個の独立タスクに展開）

## 主要設定

- `benchmark_graph` は内部で `graph_mode`（`serial` / `thread` / `async`）と `execution_mode`（`serial` / `thread` / `async`）の組み合わせを走査し、合計 **9 種類の組み合わせ**
- 同期ノードテンプレートは `graph` 経由で、非同期ノードテンプレートは `async_graph` 経由で渡す。`benchmark_graph` が列ごとに適切なテンプレートを選択する
- `serial/thread + async` の組み合わせの場合、ベンチマーク関数はバックグラウンドスレッドで同期グラフのエントリポイントを呼び出し、自身のイベントループとの競合を回避する

## 発生し得る問題

1. **Reporter はデフォルトで無効**：現在のスクリプトには `set_reporter(...)` や `add_observer(...)` の呼び出しが一切ないため、`.env` で `REPORT_HOST`/`REPORT_PORT` を設定していても**自動的には** reporter に接続しない。reporter を有効化する場合は、`bench_graph_*` の内部で明示的に `graph.set_reporter(...)` を呼び出し、かつサービスへの到達可能性を保証する必要がある。
2. **合計所要時間が長い**：`benchmark_graph` は `len(graph_modes) × len(execution_modes)` 回の完全なグラフ実行を行う。I/O 遅延を含む場合の合計時間は数分に達する可能性がある。

## 実行方法

```bash
python bench/bench_graph_mode.py
```

## パラメータ調整

### 特定テストシナリオの単独実行

> `benchmark_graph` は `async` 関数に変更されており、`bench_graph_*` はすべて `async def` である。`main_async()` または `asyncio.run()` 経由で呼び出す必要がある。

`bench/bench_graph_mode.py` の `main_async()` で特定のシナリオのみを実行できる：

```python
async def main_async() -> None:
    # await bench_graph_0()
    # await bench_graph_1()
    await bench_graph_2()

if __name__ == "__main__":
    asyncio.run(main_async())
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

> 🟢 本セクションの各表の所要時間は過去の実測データであり、ソースコードからは検証できないため、手動で確認する必要がある。うち初期の表の `process` 行は既に廃止された `stage_mode="process"` に対応し、歴史的参考としてのみ残している。

### 履歴結果 - Windows グラフモード比較（日時未記録）

> 環境：Windows、Python 3.10

#### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、12 タスク（異常境界を含む）

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

### 2026/08/05 — `start_graph_async` リファクタリング後の再実行

> 環境：Windows、Python 3.14、Reporter **無効**（HTTP タイムアウトによる所要時間への干渉を回避）
> 変更点：`benchmark_graph` が `async` 関数に変更、`async` execution mode は `start_graph` ではなく `start_graph_async` を使用

#### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、12 タスク（異常境界を含む）

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.36s | 1.38s | 1.39s |
| **thread** | 8.11s | 1.39s | 1.38s |

- I/O 部分（`sleep_1`）の比率が高くない場合でも、`thread` と `async` は依然として約 **6x** の高速化をもたらす
- このシナリオでは `stage_mode` の影響は小さい（スレッドレイアウトのオーバーヘッドがタスク実行時間によって隠される）

#### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 69.04s | 12.03s | 6.05s |
| **thread** | 19.02s | 6.02s | 8.06s |

- 最適組み合わせ：`serial`+`async`（6.05s）。最悪 `serial`+`serial`（69.04s）比で **11.4x** 高速
- `stage_mode=thread` + `execution_mode=async`（8.06s）は逆に `serial`+`async`（6.05s）より遅い。理由は thread stage 間のスレッド切り替え + async コルーチンスケジューリングによる二重オーバーヘッド
- `execution_mode=async` が I/O 集約型シナリオで初めて正しく発火（以前は誤って同期パスを通っていた）。優位性が顕著

#### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋計算、10,000 タスク

| stage_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 2.65s | 3.18s | 6.05s |
| **thread** | 2.55s | 4.64s | 5.50s |

- `serial`+`serial`（2.65s）が最速。純粋計算シナリオの結論は変わらない
- `async` は I/O 待機がないため、コルーチンスケジューリングオーバーヘッドにより約 **2.3x** の減速
- 全体として旧版（Reporter 有効）比で約 3x 高速。Reporter の HTTP タイムアウトが前ラウンドの所要時間に大きく寄与していたことが検証された

> **Reporter の影響に関する説明**：前ラウンドのデータでは Reporter サービスが起動しておらず、バックグラウンドスレッドが 5 秒ごとに HTTP リクエストのタイムアウトを待っていたため、合計所要時間が顕著に伸びていた。今回のラウンドですべての Reporter を無効化したことで、データはフレームワーク自身のスケジューリング性能をより正確に反映している。
>
> 旧版（2026/07/16 より前）では `execution_mode="async"` のとき実際には `start_graph` 同期パス（`start_stage` 内部で `asyncio.run` を呼び出す）を通っていたが、新版では `start_graph_async` 経由で正しくコルーチンパスを通るため、歴史的データは直接比較できない。

### 2026/08/17 — 9 種類組み合わせマトリックス補完後の再実行

> 環境：macOS、Python 3.14.3、Reporter **未有効化**
> 変更点：`benchmark_graph` が `graph_mode × execution_mode` の 3×3 組み合わせマトリックスを補完。本ラウンドのデータは `serial/thread/async × serial/thread/async` の完全な 9 種類組み合わせに対応

#### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、12 タスク（異常境界を含む）

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 8.17s | 1.17s | 1.16s |
| **thread** | 8.06s | 1.17s | 1.17s |
| **async**  | 8.05s | 1.17s | 1.15s |

- 3 行の差が極めて小さい。このシナリオの主導要因は依然としてノード内部の並行方式であり、図レベルの起動方式ではない
- `execution_mode=thread` と `async` はいずれも合計時間を約 1.15s–1.17s に抑えており、`serial` 列と比べて約 **7x** の向上
- `graph_mode="async"` は追加の顕著な利得をもたらしていない。この 4 ノード混合 DAG では、図スケジューリングのコストはすでにタスク実行時間に隠されている

#### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 71.19s | 12.03s | 13.03s |
| **thread** | 21.05s | 7.03s  | 6.02s  |
| **async**  | 30.07s | 7.02s  | 6.01s  |

- 最適組み合わせは `async + async`（6.01s）と `thread + async`（6.02s）で、ともにほぼ同等
- 図レベルで `serial` から `thread/async` に向上させる利得は非常に顕著。`execution_mode=serial` でも 71.19s から 21.05s または 30.07s に短縮できる
- `thread/async graph_mode` 下では `execution_mode=thread` と `async` のいずれも純直列より顕著に優位。このシナリオの主たる利益は I/O の重複と複数ノードの並行起動

#### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋計算、10,000 タスク

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 1.10s | 1.63s | 2.10s |
| **thread** | 1.10s | 1.56s | 2.41s |
| **async**  | 1.11s | 1.56s | 1.92s |

- `serial + serial` が依然として最適解であり、純粋計算型の小タスクシナリオでは直接関数呼び出しのコストが最も低い
- `execution_mode=thread` はスレッドプール送信と同期のオーバーヘッドを伴うため、全体として `serial` より遅い
- `execution_mode=async` が最も遅い。理由は依然として、コルーチン作成とスケジューリングのコストを I/O 待機で償却できないため
- このシナリオには `TaskSplitter` が含まれており、それは常に `execution_mode="serial"` に固定されている。したがってこの組のデータは「Splitter を直列入口とする混合モード」の benchmark であり、すべてのノードが厳密に同じ execution mode に切り替わるわけではない

#### 本ラウンドの総括

- `benchmark_graph` は現在、完全な `3 × 3` 組み合わせマトリックスを直接出力できる
- I/O 集約型 DAG に対しては、`graph_mode=thread/async` に `execution_mode=thread/async` を組み合わせる利得が最も顕著
- 混合型 DAG に対しては、ノード内部の並行方式が図レベルの起動方式より結果を主導する
- 純粋計算マイクロタスクに対しては、`serial + serial` が依然として最も安定しており、余分な並行層は通常スケジューリングオーバーヘッドを増幅させるだけ

> 本ラウンドのデータと 2026/08/05 の結果は列ごとに直接比較できない。一方では実行環境が Windows から macOS に変わっており、もう一方ではマトリックスが従来の不完全な組み合わせから完全な 9 マスに拡張され、`async` 列の意味も修正されている。

### 2026/08/31 — bench_graph_0 の異常入力除去後の再実行（Windows）

> 環境：Windows、Python 3.14.3、Reporter **未有効化**
> 変更点：`bench_graph_0` の入力を `range(25, 32) + [0, 27, None, 0, ""]`（異常境界を含む）から純粋な `range(25, 32)` に変更。失敗タスクのリトライパスが所要時間に与える影響を除外

#### `bench_graph_0` — 4 ノード DAG、CPU+I/O 混合、7 タスク（純粋な成功パス）

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 7.34s | 1.37s | 1.37s |
| **thread** | 7.06s | 1.38s | 1.39s |
| **async**  | 7.08s | 1.37s | 1.41s |

- 異常入力を含む旧版（serial 列約 8.1–8.4s）と比較して、失敗入力を除去すると serial 列は約 7.06–7.34s に低下する。省かれたのは失敗タスクのリトライとエラーハンドリングのコスト（約 1s）
- `thread` / `async` 列はほぼ変わらない（約 1.37–1.41s）：失敗タスク自体の実行は極めて高速（fibonacci(0) が即座にエラー）で、並行モードへの影響は無視できる
- 結論は変わらない：`graph_mode` の 3 行の差は極めて小さく、ノード内部の `execution_mode` が依然として主導要因

#### `bench_graph_1` — 6 ノード DAG、I/O 集約型（ランダム sleep）、10 タスク

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 79.05s | 12.03s | 12.10s |
| **thread** | 20.02s | 7.02s  | 6.06s  |
| **async**  | 21.03s | 8.02s  | 6.06s  |

- 最適組み合わせ：`thread + async`（6.06s）と `async + async`（6.06s）。08/17 の結論と一致
- ランダム sleep（0–2s × 全図約 60 タスク）により単一ラウンドのデータの分散が大きい（例：`serial+serial` が 74–79s の間で揺れる）。比較する際は単一ラウンドの絶対値ではなく、複数ラウンドの傾向を見るべき

#### `bench_graph_2` — 4 ノード DAG（Splitter→A→[B,C]）、純粋計算、10,000 タスク

| graph_mode \ execution_mode | serial | thread | async |
|----------------------------|--------|--------|-------|
| **serial** | 4.59s | 3.67s | 6.42s |
| **thread** | 2.96s | 3.79s | 6.82s |
| **async**  | 3.05s | 5.48s | 5.69s |

- 本ラウンドでは `thread + serial`（2.96s）が最速組み合わせであり、`serial + serial`（4.59s）が逆に遅い。歴史的複数ラウンドで `serial+serial` が常に優位（1.10s / 2.65s）だった傾向と一致しない。システム負荷または CPU 周波数の揺らぎによるものと推測され、再テストでの確認が必要
- `execution_mode=async` は依然として最も遅い（5.69–6.82s）。純粋計算シナリオにおけるコルーチンスケジューリングオーバーヘッドの結論は安定
- このシナリオには `TaskSplitter` が含まれており、常に `execution_mode="serial"` に固定されている。そのため `thread`/`async` 列は下流の A/B/C にのみ作用する

#### 本ラウンドの総括

- `bench_graph_0` 純粋化後：`execution_mode` が主導し、`graph_mode` は無関係という結論がより明確になり、失敗パスのオーバーヘッドが約 1s という定量も検証された
- I/O 集約型（bench_graph_1）：`graph_mode=thread/async` + `execution_mode=async` が依然として最適
- 純粋計算（bench_graph_2）：`async` は依然として最も遅いが、`serial+serial` と `thread+serial` の順位は本ラウンドで反転しており、単一ラウンドの揺らぎが大きい。結論は複数ラウンドを基準とすべき

> 本ラウンドの実行環境（Windows）と 2026/08/17 の macOS データは列ごとに直接比較できない。

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`benchmark_graph`）
- `python-dotenv`
- 外部サービス：Reporter サービス（オプション）
