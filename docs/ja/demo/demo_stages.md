# demo_stages.py デモ説明

## 目的

CelestialFlow における特殊 Stage ノードの使用方法を実演します：`TaskSplitter`（タスク分割）、`TaskRouter`（タスクルーティング）、`TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource`（Redis 分散トランスポート）。循環依存やデバイス間連携を含む複雑なタスクグラフを構築します。

## デモシナリオ

### `demo_splitter_0`
Web クローラーワークフローのシミュレーション：
- `GenURLs` -> URL リストの生成
- `Logger` -> クロール情報のログ記録
- `Splitter` -> URL リストを個別の URL に分割
- `Downloader` -> リソースのダウンロード
- `Parser` -> 新しい URL を解析し `GenURLs` にループバック

**グラフ構造**：循環グラフ（`parse_stage -> generate_stage`）

### `demo_splitter_1`
大規模データパケットの分割を実演します：入力 `range(int(1e5))` をリストにラップして `TaskSplitter` に渡し、下流のステージが個別にアイテムを受信・処理することで、一度にメモリに大量のタスクを読み込むことを回避します。

### `demo_redis_ack_0/1/2`
Python ローカル計算と Redis + Go Worker による外部計算の所要時間の差を比較します：
- `demo_redis_ack_0`：フィボナッチ（CPU 集約型）
- `demo_redis_ack_1`：`sum_int`（通信オーバーヘッドが支配的）
- `demo_redis_ack_2`：画像ダウンロード（I/O 集約型）

### `demo_redis_source_0`
`TaskRedisSource` が Redis からタスクを独立して読み取り、デバイス間・TaskGraph 間のデータ転送を実現する方法を実演します。

### `demo_router_0`
`TaskRouter` が奇偶性に基づいてタスクを異なる下流ノードに分配する方法を実演します。

## 主要設定

- すべてのステージはデフォルトで `stage_mode="process"`（マルチプロセス）
- `set_reporter(True)` で監視レポートを有効化
- `set_ctree(True)` でイベントトレースを有効化

## 発生しうる問題

1. **Redis 依存**：`demo_redis_*` シリーズには利用可能な Redis サービスが必要です（`.env` で `REDIS_HOST`、`REDIS_PASSWORD` を設定）。
2. **Go Worker の事前設定**：外部 Worker を使用する前に[事前設定](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期設置)を完了する必要があります。
3. **ハードコードされたネットワークパス**：`DownloadStage` と `DownloadRedisTransport` には Windows パスがハードコードされており（`X:/Download/...`）、非 Windows 環境やパスが存在しない場合に失敗します。
4. **長い実行時間**：`demo_splitter_0` の各ステージには4〜6秒のランダムスリープが含まれており、完全な実行には1分以上かかる場合があります。
5. **アサーションなし**：デモスクリプトであり、結果の正確性は検証されません。

## 実行方法

```bash
# 特定のデモを実行
python demo/demo_stages.py
```

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`TaskSplitter`、`TaskRouter`、`TaskRedisTransport`、`TaskRedisAck`、`TaskRedisSource`）
- `demo_utils`
- `python-dotenv`
- 外部サービス：Redis、CelestialTree（オプション）、Reporter（オプション）、Go Worker（オプション）
