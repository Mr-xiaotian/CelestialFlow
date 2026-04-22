# Other モジュール

## 概要

Other モジュールには、CelestialFlow フレームワークの拡張コンポーネントと外部統合が含まれています。これらのコンポーネントはコアフレームワークには属しませんが、重要な拡張機能を提供します。主に CelestialTree クライアントと Go Worker の2つのコンポーネントで構成され、それぞれタスクの来歴追跡とクロス言語タスク実行に使用されます。

## ファイル詳細説明

### 1. ctree_client.md - CelestialTree クライアント

**役割**: CelestialTree イベントソーシングシステムと統合し、タスクの全チェーン追跡とイベント記録を実現します。

**コア機能**:
- **イベント記録**: タスクのライフサイクル中の重要なイベント（入力、成功、失敗、リトライ、分裂、ルーティングなど）を自動記録します
- **データリネージ追跡**: 結果のデータソースと生成パスをクエリします
- **エラー根本原因の特定**: 失敗タスクの完全なコールチェーンを追跡します
- **実行ツリーの可視化**: タスク実行のコールツリー構造を生成します

**主な特徴**:
- CelestialTree サービスと統合し、HTTP および gRPC 通信をサポートします
- 手動の計装なしで自動的にイベントを発行します
- 簡素化された来歴クエリインターフェースを提供します
- タスクの分裂、ルーティング、重複検出などの複雑なシナリオをサポートします

**使用パターン**:
```python
# CelestialTree クライアントの設定
graph.set_ctree(
    use_ctree=True,
    host="127.0.0.1",
    http_port=7777,
    grpc_port=7778
)

# 来歴情報のクエリ
trace_str = graph.get_stage_input_trace(stage_tag="Stage1")
error_trace = graph.get_error_trace(error_id=12345)
```

### 2. go_worker.md - Go Worker タスクコンシューマー

**役割**: クロス言語タスク実行のための、軽量でスケーラブルな Redis ベースのタスクコンシューマー（Worker Pool）です。

**コア機能**:
- **タスク消費**: Redis キューからタスクを継続的に消費します
- **並行実行**: 制御可能な並行度でタスクを実行します
- **結果の書き戻し**: 実行結果を Redis に書き戻します
- **クロス言語サポート**: TaskGraph の Go 言語実行ノードとして機能します

**アーキテクチャの特徴**:
- **Worker Pool パターン**: goroutine とチャネルを使用した並行制御
- **自動再接続メカニズム**: Redis 接続失敗時の指数バックオフリトライをサポートします
- **プラグイン可能な設計**: Parser と Processor をカスタマイズおよび拡張できます
- **汎用タスク構造**: JSON 形式のタスクペイロードを使用します

**主要コンポーネント**:
- **TaskParser**: タスクペイロードを解析し、Processor が必要とする形式に変換します
- **TaskProcessor**: ビジネスロジックを実行し、計算結果を返します
- **Worker Pool**: 並行実行とリソース制御を管理します

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

## モジュールの関連

### コアフレームワークとの関係

1. **CelestialTree クライアント**:
   - `TaskGraph` と密接に統合され、タスクイベントを自動記録します
   - `observability` モジュールのイベント発行メカニズムに依存します
   - `web` モジュールに来歴データのサポートを提供します

2. **Go Worker**:
   - `runtime` モジュールの `TaskRedisTransport` および `TaskRedisAck` ノードと連携します
   - Redis を介して Python 側の TaskGraph と通信します
   - スタンドアロンコンポーネントとして使用でき、コアフレームワークへの依存は必須ではありません

### コンポーネント間の連携

```
TaskGraph (Python) → Redis → Go Worker → Redis → TaskGraph (Python)
    ↓
CelestialTree Client → CelestialTree Service
```

1. **タスク実行フロー**:
   - TaskGraph がタスクを生成し、Redis に書き込みます
   - Go Worker が Redis からタスクを消費して実行します
   - 実行結果が Redis に書き戻され、TaskGraph が結果を読み取ります
   - CelestialTree クライアントがプロセス全体のイベントを記録します

2. **データフロー**:
   - タスクデータは Redis を介して Python と Go の間で転送されます
   - イベントデータは HTTP/gRPC を介して CelestialTree に送信されます
   - 来歴クエリはクライアント API を通じて CelestialTree から取得されます

## アーキテクチャの特徴

### 1. 疎結合設計
- 各コンポーネントを独立してデプロイおよび使用できます
- 標準プロトコル（Redis、HTTP）による通信
- 言語バインディングなし、多言語拡張をサポートします

### 2. 可観測性の強化
- CelestialTree がきめ細かなタスクの来歴を提供します
- エラー追跡とパフォーマンス分析をサポートします
- フレームワークの監視メトリクスを補完します

### 3. パフォーマンス最適化
- Go Worker が高パフォーマンスのタスク実行を提供します
- 並行制御によりリソースの枯渇を防止します
- 自動再接続によりシステムの安定性を確保します

## 使用パターン

### 1. フルチェーン追跡パターン
```python
# CelestialTree 追跡を有効にする
graph.set_ctree(use_ctree=True)

# タスクグラフを実行する
graph.start_graph(init_tasks)

# タスクの来歴をクエリする
trace = graph.get_stage_input_trace("ProcessingStage")
```

### 2. クロス言語実行パターン
```python
# Python 側：Redis トランスポートノードを定義する
redis_sink = TaskRedisTransport(key="tasks:input")
redis_ack = TaskRedisAck(key="tasks:output")

# Go 側：Worker Pool を起動してタスクを消費する
# go_worker/main.go で同じ Redis キーを設定する
```

### 3. ハイブリッドパターン
CelestialTree 追跡と Go Worker 実行を同時に使用して、完全な可観測性と高パフォーマンスの実行能力を実現します。

## ベストプラクティス

### 1. CelestialTree の設定
- 本番環境ではスタンドアロンの CelestialTree サービスをデプロイしてください
- タスク量に応じてイベントサンプリングレートを調整してください
- 期限切れのイベントデータを定期的にクリーンアップしてください

### 2. Go Worker のデプロイ
- タスクの種類に応じて適切な並行度を選択してください
- Redis の接続状態とキューの長さを監視してください
- 特定のビジネスロジック用にカスタム Processor を実装してください

### 3. エラー処理
- Go Worker に包括的なエラーログを追加してください
- タスクのリトライとデッドレターキューのメカニズムを実装してください
- CelestialTree の接続状態を監視してください

### 4. パフォーマンスチューニング
- Redis のコネクションプールサイズを調整してください
- タスクペイロードのシリアライズ形式を最適化してください
- ハードウェアリソースに応じて Worker の並行数を調整してください

## 拡張の提案

### 1. 新しい Processor の追加
`go_worker/worker/processors.go` に新しい Processor 関数を追加して、より多くの種類のタスク処理をサポートします。

### 2. カスタム Parser
カスタム TaskParser を実装して、複雑なタスク形式の解析をサポートします。

### 3. 監視の統合
Go Worker のメトリクスをフレームワークの監視システムに統合し、統一された可観測性を実現します。

### 4. 多言語サポート
Go Worker のパターンを参考に、他の言語（Java、Rust など）の Worker コンポーネントを実装します。

## 注意事項

1. **バージョン互換性**: CelestialTree クライアントとサーバーのバージョンの互換性を確認してください
2. **ネットワーク遅延**: Redis と CelestialTree のネットワーク遅延は全体的なパフォーマンスに影響します
3. **リソース管理**: リソースの競合を避けるために、Worker の並行度を適切に設定してください
4. **データ一貫性**: Redis のトランザクションとアトミック操作の使用に注意してください
5. **セキュリティの考慮**: Redis と CelestialTree のアクセス認証情報を保護してください
