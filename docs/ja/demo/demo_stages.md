# demo_stages.py デモ説明

> 📅 最終更新日: 2026/05/15

## 目的

CelestialFlow の特殊 Stage ノードの使用方法をデモンストレーションします：`TaskSplitter`（タスク分割）、`TaskRouter`（タスクルーティング）、`TaskRedisTransport` / `TaskRedisAck` / `TaskRedisSource`（Redis 分散トランスポート）。循環依存関係やクロスデバイス連携を含む複雑なタスクグラフを構築します。

## カスタムサブクラス

- `DownloadRedisTransport`: `TaskRedisTransport` を継承し、`get_args` メソッドをオーバーライドして `/tmp/` パスを `X:/Download/download_go/` に置換（Go Worker 用）。
- `DownloadStage`: `TaskStage` を継承し、`get_args` メソッドをオーバーライドして `/tmp/` パスを `X:/Download/download_py/`に置換（Python ローカルダウンロード用）。

## デモシナリオ

### `demo_splitter_0`
クローラーワークフローのシミュレーション：
- `GenURLs` → URL リストを生成
- `Logger` → クロール情報をログ記録
- `Splitter` → URL リストを個別の URL に分割
- `Downloader` → リソースをダウンロード
- `Parser` → 新しい URL を解析し `GenURLs` にループバック

**グラフ構造**: 循環グラフ（`parse_stage → generate_stage`）

### `demo_splitter_1`
大データパッケージの分割をデモンストレーション：入力 `range(int(1e5))` をリストでラップして `TaskSplitter` に渡し、下流ステージが1つずつ受信・処理することで、一度に大量のタスクをメモリに読み込むことを回避します。

### `demo_redis_ack_0/1/2`
Python ローカル計算と Redis + Go Worker 外部計算の所要時間を比較：
- `demo_redis_ack_0`: フィボナッチ（CPU 集約型）
- `demo_redis_ack_1`: `sum_int`（通信オーバーヘッド主導）
- `demo_redis_ack_2`: 画像ダウンロード（I/O 集約型）

### `demo_redis_source_0`
`TaskRedisSource` が Redis から独立してタスクを読み取り、クロスデバイス/クロス TaskGraph のデータ転送を実現することをデモンストレーションします。

### `demo_router_0`
`TaskRouter` が奇偶性に基づいてタスクを異なる下流ノードに分配することをデモンストレーションします。

## 主要設定

- すべての stage のデフォルトは `stage_mode="thread"`（マルチスレッド）
- `set_reporter(True)` でモニタリングレポートを有効化
- `set_ctree(True)` でイベントトレーシングを有効化

## 起こりうる問題

1. **Redis 依存**: `demo_redis_*` シリーズは利用可能な Redis サービスが必要です（`.env` で `REDIS_HOST`、`REDIS_PASSWORD` を設定）。
2. **Go Worker の事前設定**: 外部 Worker の使用には[事前設定](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/docs/reference/other/go_worker.md#前期設置)の完了が必要です。
3. **ハードコードされたネットワークパス**: `DownloadStage` と `DownloadRedisTransport` には Windows パスのハードコード（`X:/Download/...`）が含まれており、非 Windows 環境やパスが存在しない場合に失敗します。
4. **長時間実行**: `demo_splitter_0` の各ステージには4-6秒のランダム sleep が含まれ、完全な実行は1分を超える場合があります。
5. **アサーションなし**: デモスクリプトであり、結果の正確性は検証しません。

## 実行方法

```bash
# 特定のデモを実行
python demo/demo_stages.py
```

## 依存関係

- `celestialflow`（`TaskGraph`、`TaskStage`、`TaskChain`、`TaskSplitter`、`TaskRouter`、`TaskRedisTransport`、`TaskRedisAck`、`TaskRedisSource`）
- `demo_utils`
- `python-dotenv`
- 外部サービス: Redis、CelestialTree（オプション）、Reporter（オプション）、Go Worker（オプション）
