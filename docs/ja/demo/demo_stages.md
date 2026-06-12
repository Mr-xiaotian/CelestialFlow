# demo_stages.py デモ説明

> 📅 最終更新日: 2026/06/11

## 目標

CelestialFlow における特殊 Stage ノードの使用方法をデモします：`TaskSplitter`（タスク分割）、`TaskRouter`（タスクルーティング）、`TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource`（Redis 分散転送）。循環依存とクロスデバイス協調を含む複雑なタスクグラフを構築します。

## デモシナリオ

### `demo_splitter_0`
クローラーワークフローのシミュレーション：

```mermaid
flowchart TD
    GenURLs["GenURLs<br/>URL リストを生成"] -->|直接出力| Logger["Logger<br/>クロール情報を記録"]
    GenURLs -->|直接出力| Splitter["Splitter<br/>URL リストを単一 URL に分割"]
    Splitter -->|単一 URL| Downloader["Downloader<br/>リソースをダウンロード"]
    Splitter -->|単一 URL| Parser["Parser<br/>新しい URL を解析"]
    Parser -.->|ループバック| GenURLs
```

- `GenURLs` → URL リストを生成
- `Logger` → クロール情報を記録
- `Splitter` → URL リストを単一 URL に分割
- `Downloader` → リソースをダウンロード
- `Parser` → 新しい URL を解析し、`GenURLs` にループバック

**グラフ構造**：循環グラフ（`parse_stage → generate_stage`）

### `demo_splitter_1`
大規模データ分割のデモ：入力 `range(int(1e5))` がリストにラップされて `TaskSplitter` に渡され、下流が 1 つずつ受信処理することで、一度に大量のタスクをメモリにロードするのを回避します。

### `demo_redis_ack_0/1/2`
Python ローカル計算と Redis + Go Worker 外部計算の時間差を比較：

```mermaid
flowchart TB
    subgraph Python["Python ローカル計算"]
        direction LR
        Start["Start<br/>sleep_1"] -->|直接発行| Compute["計算ノード<br/>Fibonacci / Sum / Download"]
        Compute --> Ack["RedisAck<br/>結果確認"]
    end

    subgraph GoWorker["Redis + Go Worker 外部計算"]
        direction LR
        StartGo["Start<br/>sleep_1"] -->|書き込み| Transport["RedisTransport<br/>key: input"]
        Transport -.->|Go Worker 消費| GoCalc["Go Worker<br/>外部計算"]
        GoCalc -.->|Go Worker 書き込み| GoAck["RedisAck<br/>key: output"]
    end

    PythonStart["Start"] --> Python
    PythonStart --> GoWorker
```

| シナリオ | 計算タイプ | Python ローカルノード | Go Worker ノード |
|------|---------|----------------|----------------|
| `demo_redis_ack_0` | CPU 集中 | `Fibonacci` | フィボナッチ計算 |
| `demo_redis_ack_1` | 通信オーバーヘッド主導 | `Sum`（`sum_int`） | 合計計算 |
| `demo_redis_ack_2` | I/O 集中 | `Download`（`download_to_file`） | 画像ダウンロード（外部 Worker） |

> 図中の破線矢印はプロセス/デバイス間のデータフローを示します。すべての `demo_redis_ack_*` の Python パスと Go Worker パスは同じ `Start` ノードを共有します：`graph.connect([start_stage], [redis_tranport, compute_stage])`。

### `demo_redis_source_0`
`TaskRedisSource` が Redis から独立してタスクを読み取り、クロスデバイス/クロス TaskGraph のデータ転送を実現するデモです。

### `demo_router_0`
`TaskRouter` が偶奇性に基づいてタスクを異なる下流ノードに振り分けるデモです。

```mermaid
flowchart LR
    Origin["Origin<br/>RouterWrapper"] -->|"(target, n)"| Router["Router<br/>stage_mode=serial"]
    Router -->|偶数 n % 2 == 0| StageA["StageA<br/>thread | 2 workers"]
    Router -->|奇数 n % 2 != 0| StageB["StageB<br/>thread | 2 workers"]
```

ルーティングロジック：`Origin` ステージの `RouterWrapper` が入力 `n` の偶奇性に基づいて `(target, n)` タプルを生成し、`Router` が `target` フィールドに従ってタスクを `StageA`（偶数）または `StageB`（奇数）に振り分けます。

## 主要設定

- すべての stage はデフォルト `stage_mode="thread"`（マルチスレッド）
- `set_reporter(True)` で監視レポートを有効化
- `set_ctree(True)` でイベントトレースを有効化

## 発生しうる問題

1. **Redis 依存**：`demo_redis_*` シリーズは利用可能な Redis サービスが必要です（`.env` に `REDIS_HOST`、`REDIS_PASSWORD` を設定）。
2. **Go Worker 事前設定**：外部 Worker を使用する前に [事前設定](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期设置) を完了する必要があります。
3. **パスのハードコード**：`demo_redis_ack_2` のダウンロードリンクはサンプル URL であり、実際のネットワーク環境やパスでは失敗する可能性があります。
4. **長時間実行**：`demo_splitter_0` の各ステージには 4〜6 秒のランダム sleep が含まれ、完全な実行には 1 分以上かかる場合があります。
5. **アサーションなし**：デモスクリプトであり、結果の正確性は検証しません。

## 実行方法

```bash
# デフォルトデモ（demo_splitter_0）を実行
python demo/demo_stages.py

# main() を変更して他のシナリオを実行可能
# 例：demo_splitter_0() を demo_router_0() に置き換え
```

## 想定される動作

### `demo_splitter_0`（クローラーワークフロー）

URL 生成後に Splitter で分割され、Downloader と Parser が並行処理し、Parser の結果が Generator にループバックされます：

```
[GenURLs] Generated 3 URLs
[Splitter] Splitting 3 URLs...
[Downloader] Downloading url_0...
[Parser] Parsing url_0...
[Logger] Logging: url_0
[Downloader] Downloading url_1...
...
```

> ランダム sleep（4〜6 秒）を含み、総実行時間は 1 分以上かかる場合があります。

### `demo_router_0`（偶奇ルーティング）

Origin が入力の偶奇性に基づいて `(target, n)` を生成し、Router が StageA（偶数）または StageB（奇数）に振り分けます：

```
[Origin] Input: 0 -> RouterWrapper(0) -> ('stage_a', 0)
[Origin] Input: 1 -> RouterWrapper(1) -> ('stage_b', 1)
[Router] Routing 0 to stage_a
[Router] Routing 1 to stage_b
[StageA] Received: 0
[StageB] Received: 1
...
```

### `demo_redis_ack_0/1/2`（Redis 分散計算）

Python ローカル計算と Go Worker 外部計算が並行実行され、結果がそれぞれ Redis Ack に書き込まれます：

```
[Fibonacci] Computing fibonacci for n=10...
[RedisTransport] Writing 10 to Redis key 'input:0'
[RedisAck] Acknowledging fibonacci result: 55
...
```

> Redis と Go Worker を事前に起動する必要があります（[事前設定] 参照）。自動停止しないため、手動で Ctrl+C で終了してください。

### `demo_splitter_1`（大規模データ分割）

`range(100000)` をリストにラップして Splitter に渡し、1 つずつ下流に出力して処理します。追加の出力ログはありません。

## 依存

- `celestialflow`（`TaskGraph`、`TaskStage`、`TaskChain`、`TaskSplitter`、`TaskRouter`、`TaskRedisTransport`、`TaskRedisAck`、`TaskRedisSource`）
- `demo_utils`
- `python-dotenv`
- 外部サービス：Redis、CelestialTree（オプション）、Reporter（オプション）、Go Worker（オプション）
