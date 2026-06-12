# Other モジュール

> 📅 最終更新日: 2026/04/22

## 概要

Other モジュールは CelestialFlow フレームワークの拡張コンポーネントと外部統合を含みます。これらのコンポーネントはコアフレームワークには属しませんが、重要な拡張機能を提供します。主に CelestialTree クライアントと Go Worker の 2 つのコンポーネントで構成され、それぞれタスクのトレーサビリティ追跡とクロス言語タスク実行に使用されます。

## ファイル詳細説明

### 1. ctree_client.md - CelestialTree クライアント

**役割**: CelestialTree イベントソーシングシステムを統合し、タスクの全リンクトレースとイベント記録を実現します。

**コア機能**:
- **イベント記録**: タスクライフサイクル中の重要なイベント（入力、成功、失敗、リトライ、分割、ルーティングなど）を自動記録
- **データリネージ追跡**: 結果のデータソースと生成パスを照会
- **エラー根本原因特定**: エラータスクの完全なコールチェーンを追跡
- **実行ツリー可視化**: タスク実行のコールツリー構造を生成

**主な特徴**:
- CelestialTree サービスと統合し、HTTP および gRPC 通信をサポート
- 自動イベント発行、手動の計装不要
- 簡略化されたトレーサビリティ照会インターフェースを提供
- タスク分割、ルーティング、重複検出などの複雑なシナリオをサポート

**使用パターン**:
```python
# CelestialTree クライアントの設定
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)

# トレーサビリティ情報の照会
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
error_trace = graph.get_error_trace(error_id=12345)
```

### 2. go_worker.md - Go Worker タスクコンシューマー

**役割**: 軽量で並行拡張可能な Redis ベースのタスクコンシューマー（Worker Pool）。クロス言語タスク実行に使用されます。

**コア機能**:
- **タスク消費**: Redis キューから継続的にタスクを消費
- **並行実行**: 制御可能な並行度でタスクを実行
- **結果書き戻し**: 実行結果を Redis に書き戻し
- **クロス言語サポート**: TaskGraph の Go 言語実行ノードとして機能

**アーキテクチャの特徴**:
- **Worker Pool パターン**: goroutine と channel を使用して並行制御を実現
- **自動再接続メカニズム**: Redis 接続失敗時の指数バックオフリトライをサポート
- **プラグ可能設計**: Parser と Processor をカスタム拡張可能
- **汎用タスク構造**: JSON 形式のタスクペイロードを使用

**主要コンポーネント**:
- **TaskParser**: タスクペイロードを解析し、Processor が必要とする形式に変換
- **TaskProcessor**: ビジネスロジックを実行し、計算結果を返す
- **Worker Pool**: 並行実行とリソース制御を管理

**使用パターン**:
```go
// Worker Pool の起動
worker.StartWorkerPool(
    ctx,
    rdb,
    "testFibonacci:input",  // Redis 入力キュー
    "testFibonacci:output", // Redis 出力ハッシュ
    worker.ParseListTask,   // タスクパーサー
    worker.Fibonacci,       // タスクプロセッサー
    4,                      // 並行度
)
```

## モジュール連携

### コアフレームワークとの関係

1. **CelestialTree クライアント**:
   - `TaskGraph` と密接に統合され、タスクイベントを自動記録
   - `observability` モジュールのイベント発行メカニズムに依存
   - `web` モジュールにトレーサビリティデータのサポートを提供

2. **Go Worker**:
   - `runtime` モジュールの `TaskRedisTransport` および `TaskRedisAck` ノードと連携
   - Redis 経由で Python 側の TaskGraph と通信
   - 独立したコンポーネントとして使用可能で、コアフレームワークへの依存は必須ではない

### コンポーネント間連携

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **タスク実行フロー**:
   - TaskGraph がタスクを生成し Redis に書き込み
   - Go Worker が Redis からタスクを消費して実行
   - 実行結果を Redis に書き戻し、TaskGraph が結果を読み取り
   - CelestialTree クライアントがプロセス全体のイベントを記録

2. **データフロー**:
   - タスクデータは Redis 経由で Python と Go の間で受け渡し
   - イベントデータは HTTP/gRPC 経由で CelestialTree に送信
   - トレーサビリティ照会はクライアント API 経由で CelestialTree から取得

## アーキテクチャの特徴

### 1. 疎結合設計
- 各コンポーネントは独立してデプロイ・使用可能
- 標準プロトコル（Redis、HTTP）で通信
- 言語バインディングなし、多言語拡張をサポート

### 2. 可観測性の強化
- CelestialTree が細粒度のタスクトレーサビリティを提供
- エラー追跡とパフォーマンス分析をサポート
- フレームワークの監視指標と補完

### 3. パフォーマンス最適化
- Go Worker が高性能なタスク実行を提供
- 並行制御によりリソース枯渇を防止
- 自動再接続によりシステムの安定性を保証

## 使用パターン

### 1. 全リンクトレースモード
```python
# CelestialTree トレースを有効化
graph.set_ctree(use_ctree=True)

# タスクグラフを実行
graph.start_graph(init_tasks)

# タスクトレーサビリティを照会
trace = graph.get_stage_input_trace("ProcessingStage")
```

### 2. クロス言語実行モード
```python
# Python 側：Redis 転送ノードを定義
redis_sink = TaskRedisTransport(key="tasks:input")
redis_ack = TaskRedisAck(key="tasks:output")

# Go 側：Worker Pool を起動してタスクを消費
# go_worker/main.go で同じ Redis key を設定
```

### 3. ハイブリッドモード
CelestialTree トレースと Go Worker 実行を同時に使用し、完全な可観測性と高性能な実行能力を獲得します。

## ベストプラクティス

### 1. CelestialTree 設定
- 本番環境では独立した CelestialTree サービスをデプロイ
- タスク量に応じてイベントサンプリングレートを調整
- 期限切れのイベントデータを定期的にクリーンアップ

### 2. Go Worker デプロイ
- タスクタイプに応じて適切な並行度を選択
- Redis 接続状態とキュー長を監視
- 特定のビジネスロジックを処理するカスタム Processor を実装

### 3. エラー処理
- Go Worker に充実したエラーログを追加
- タスクリトライとデッドレターキューメカニズムを実装
- CelestialTree 接続状態を監視

### 4. パフォーマンスチューニング
- Redis 接続プールサイズを調整
- タスクペイロードのシリアライズ形式を最適化
- ハードウェアリソースに応じて Worker 並行数を調整

## 拡張提案

### 1. 新しい Processor の追加
`go_worker/worker/processors.go` に新しい Processor 関数を追加し、より多くのタスクタイプの処理をサポートします。

### 2. カスタム Parser
カスタム TaskParser を実装し、複雑なタスク形式の解析をサポートします。

### 3. 監視統合
Go Worker の指標をフレームワークの監視システムに統合し、統一された可観測性を実現します。

### 4. 多言語サポート
Go Worker のパターンを参考に、他の言語（Java、Rust など）の Worker コンポーネントを実装します。

## 注意事項

1. **バージョン互換性**: CelestialTree クライアントとサーバーのバージョン互換性を確認してください
2. **ネットワーク遅延**: Redis と CelestialTree のネットワーク遅延が全体のパフォーマンスに影響します
3. **リソース管理**: Worker 並行度を適切に設定し、リソース競合を回避してください
4. **データ一貫性**: Redis トランザクションとアトミック操作の使用に注意してください
5. **セキュリティ考慮**: Redis と CelestialTree のアクセス認証情報を保護してください
