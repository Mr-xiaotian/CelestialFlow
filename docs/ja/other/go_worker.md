# Go Worker

> 📅 最終更新日: 2026/04/22

Go Worker は **軽量で、並行拡張可能な、Redis ベースのタスクコンシューマー（Worker Pool）** です。
その設計目標は次の 2 つだけです：

1. **Redis のタスクキューから継続的にタスクを消費すること**
2. **制御可能な並行度でタスクを実行し、結果を Redis に書き戻すこと**

このコンポーネントは多くの場合 **TaskGraph のクロス言語実行ノード** として使用されます：
Python の TaskGraph がタスクの生成とスケジューリングロジックの決定を担当し、Go Worker が計算集中型または IO 集中型のステップの実行に専念します。ただし、両者は完全に独立しており、go-worker は単独で実行することも、他のシステムで再利用することもできます。

## 事前設定

1. Redis サービスを起動する
`TaskRedis*` 系ノードを実行する際は、先に Redis サービスを起動する必要があります。

2. 環境変数を設定する
次に、ルートディレクトリに `.env` ファイルを作成し、以下の形式で入力します：

```env
# .env
# Redis サービスアドレス
REDIS_HOST=127.0.0.1
# Redis サービスポート
REDIS_PORT=6379
# Redis サービスパスワード（ない場合は空欄）
REDIS_PASSWORD=your_redis_password
```

3. go_worker を設定する

次に [go_worker main.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/main.go) を開きます。Redis の host と port は環境変数の設定を自動的に読み取ります。設定が必要なのは、タスク入力の key と結果出力の key、および使用する実行関数の選択のみです。

```go
err := godotenv.Load()
if err != nil {
    fmt.Println("No .env file found, using system env")
}

redisHost := os.Getenv("REDIS_HOST")
redisPort := os.Getenv("REDIS_PORT")
redisPassword := os.Getenv("REDIS_PASSWORD")

rdb := redis.NewClient(&redis.Options{
    Addr:     redisHost + ":" + redisPort,
    Password: redisPassword,
    DB:       0,
})

worker.StartWorkerPool(
  ctx,
  rdb,
  "testFibonacci:input",  // Redis 内のタスク入力 List
  "testFibonacci:output", // Redis 内の結果書き込み先 Hash
  worker.ParseListTask,
  worker.Fibonacci,
  4,
)
```

ここでは test_redis_ack_0 実行時の設定を例にしています。`testFibonacci:input` と `testFibonacci:output` は test_redis_ack_0 内の `TaskRedis*` の key 値と一致させる必要があります。

```python
# test_redis_ack_0
redis_sink = TaskRedisTransport(key="testFibonacci:input", host=redis_host, password=redis_password)
redis_ack = TaskRedisAck(key="testFibonacci:output", host=redis_host, password=redis_password)
```

同時に [go_worker processor.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/worker/processor.go) で使用する Go 関数を選択します。

4. go_worker を実行する

その後、以下を実行します：

```bash
make run_go_worker
```

go_worker が起動し Redis キューの監視を開始します。これで pytest を正常に実行できます。

## ✨ 機能特性

* **Worker Pool 並行実行**、`chan` + `WaitGroup` を使用して最大並行数を制御
  （ソースコードは `StartWorkerPool` を参照）
* **自動再接続と指数バックオフメカニズム（backoff）**、Redis が不安定でも自動復旧
* **タスク構造の汎用化**：タスクは JSON でパッケージ化されて Redis に送信
  （構造は `TaskPayload` を参照）
* **Parser / Processor のプラグ可能設計**：ユーザーはタスクの解析方法と処理方法を自由に定義可能
* **結果を Redis Hash に書き戻し**、外部システムがタスク実行状況を照会しやすい
* **サンプル Processor（Sum / Add100 / Fibonacci / DownloadToFile）** を複数提供
  （processors.go を参照）

## 📦 タスク構造の説明（TaskPayload）

各タスクは JSON 形式で Redis list に書き込まれます：

```json
{
  "id": "task-001",
  "task": [1, 2, 3]
}
```

Go Worker はまず JSON を取り出し、次に：

* Parser を使用して task フィールドを Processor が求める型に変換
* Processor が計算結果を返す
* 最終結果を Redis Hash に書き込み：`HSET output_key id {...}`

データ構造定義は以下の通りです（types.go）：

```go
type TaskPayload struct {
	ID   string `json:"id"`
	Task any    `json:"task"`
}
```

Parser と Processor のシグネチャ：

```go
type TaskParser func(any) ([]any, error)
type TaskProcessor func([]any) (any, error)
```

この設計により：

* タスク形式を自由に拡張可能
* Processor はビジネスロジックに専念し、JSON や Redis を気にする必要がない

## 🏗 Worker Pool コアロジックの概要

コアロジックは `StartWorkerPool`（worker.go）にあります。
主なフロー：

1. `BLPop` で Redis 入力タスクをブロッキング待機
2. タスクを解析 → goroutine に投入
3. `sem := make(chan struct{}, concurrency)` で並行上限を実現
4. Processor を実行
5. 結果を Redis Hash に書き込み
6. 実行時間を表示

疑似フローチャートは次のように理解できます：

```
while true:
    raw = BLPOP(input_key)
    payload = JSON デコード

    acquire semaphore
    go:
        parse(payload.task)
        result = processor()
        HSET(output_key, payload.id, result)
        release semaphore
```

設計はシンプルで堅牢、拡張も容易です。

## 🧩 カスタムタスク：Parser と Processor

### パーサー（Parser）

例えば、公式提供のリストパーサー（parse list task）：

```go
func ParseListTask(data any) ([]any, error) {
    list, ok := data.([]any)
    if !ok {
        return nil, fmt.Errorf("task should be a list, got %T", data)
    }
    return list, nil
}
```

### Processor（ビジネスロジック）

例えば、合計計算：

```go
func Sum(args []any) (any, error) {
    var sum int
    for _, a := range args {
        sum += int(a.(float64))
    }
    return sum, nil
}
```

画像処理、テキスト分析、外部インターフェース呼び出しなど、独自の processor を簡単に実装できます。

## 🧵 TaskGraph との関係（オプション）

TaskGraph は **Python タスクグラフ実行フレームワーク** であり、以下を得意とします：

* 複雑な DAG の構築
* 依存関係の管理
* タスクフロー全体の制御

一方 Go Worker は以下を得意とします：

* **単一ノードの高性能タスク** の実行
* Redis 内で TaskGraph と通信
* 言語に依存しない Worker ノードとして機能

TaskGraph を総監督、Go Worker を素早く登壇し敏捷に行動する実行者と想像してください。両者は連携可能であり、独立して使用することもできます。

## 📁 サンプル Processor リスト（processors.go）

これらのサンプルは Worker の使用方法の理解と、TaskGraph のクロス言語ノードのデバッグに役立ちます：

* `Sum`：合計計算（例：バッチ計算）
* `Add100`：単一数値に 100 を加算
* `Fibonacci`：再帰版フィボナッチ
* `DownloadToFile`：ファイルをローカルにダウンロード（IO サンプル）

すべてのソースファイルは processors.go を参照してください。

## 🧪 テスト方法

Redis で手動でタスクを push してテストできます：

```sh
redis-cli LPUSH GoSum[_trans_redis]:input '{"id":"t1","task":[3,4,5]}'
```

その後、出力を確認：

```sh
redis-cli HGET GoSum[_trans_redis]:output t1
```

以下のような結果が表示されます：

```json
{"status":"success","result":12}
```
