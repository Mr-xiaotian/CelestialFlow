# Go Worker

Go Worker は **軽量でスケーラブルな、Redis ベースのタスクコンシューマー（Worker Pool）** です。
設計目標は2つだけです：

1. **Redis のタスクキューからタスクを継続的に消費すること**
2. **制御可能な並行度でタスクを実行し、結果を Redis に書き戻すこと**

このコンポーネントは **TaskGraph のクロス言語実行ノード** として使用されることが多いです：
Python の TaskGraph がタスクの生成とスケジューリングロジックを担当し、Go Worker は計算集約型または IO 集約型のステップの実行に集中します。ただし、両者は完全に独立しています。go-worker は単独で実行することも、他のシステムで再利用することもできます。

## 事前準備

1. Redis サービスの起動
`TaskRedis*` 系のノードを実行する前に、まず Redis サービスを起動する必要があります。

2. 環境変数の設定
次に、ルートディレクトリに .env ファイルを作成し、以下の形式で記入します：

```env
# .env
# Redis サーバーアドレス
REDIS_HOST=127.0.0.1
# Redis サーバーポート
REDIS_PORT=6379
# Redis サーバーパスワード、ない場合は空白にします
REDIS_PASSWORD=your_redis_password
```

3. go_worker の設定

次に [go_worker main.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/main.go) を開きます。Redis の host と port は環境変数から自動的に読み込まれます。設定が必要なのは、タスク入力のキー、結果出力のキー、および使用する実行関数の選択だけです。

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
  "testFibonacci:input",  // Redis の入力 List
  "testFibonacci:output", // Redis の出力 Hash
  worker.ParseListTask,
  worker.Fibonacci,
  4,
)
```

ここでは test_redis_ack_0 を実行する際の設定を例として使用しています。`testFibonacci:input` と `testFibonacci:output` は test_redis_ack_0 の `TaskRedis*` のキー値と一致する必要があります。

```python
# test_redis_ack_0
redis_sink = TaskRedisTransport(key="testFibonacci:input", host=redis_host, password=redis_password)
redis_ack = TaskRedisAck(key="testFibonacci:output", host=redis_host, password=redis_password)
```

同時に [go_worker processor.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/worker/processor.go) で使用する Go 関数を選択します。

4. go_worker の実行

次に以下を実行します：

```bash
make run_go_worker
```

go_worker が起動し、Redis キューのリスニングを開始します。この時点で、pytest を正常に実行できます。

## 機能特性

* **Worker Pool 並行実行**、`chan` + `WaitGroup` を使用して最大並行数を制御します
  （ソースは `StartWorkerPool` を参照）
* **自動再接続と指数バックオフメカニズム**、Redis が不安定でも自動的に回復します
* **汎用タスク構造**：タスクは JSON でパッケージ化され Redis に送信されます
  （構造は `TaskPayload` を参照）
* **プラグイン可能な Parser / Processor**：ユーザーはタスクの解析方法と処理方法を自由に定義できます
* **結果は Redis Hash に書き込まれ**、外部システムがタスクの実行状況を照会しやすくなります
* いくつかの **サンプル Processor（Sum / Add100 / Fibonacci / DownloadToFile）** を提供します
  （processors.go を参照）

## タスク構造の説明（TaskPayload）

各タスクは JSON 形式で Redis リストに書き込まれます：

```json
{
  "id": "task-001",
  "task": [1, 2, 3]
}
```

Go Worker は JSON を取得した後、以下を行います：

* Parser を使用して task フィールドを Processor が期待する型に変換します
* Processor が計算を担当し、結果を返します
* 最終結果は Redis Hash に書き込まれます：`HSET output_key id {...}`

データ構造の定義（types.go）：

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

この設計により、以下が可能になります：

* タスク形式を自由に拡張できます
* Processor は JSON や Redis を気にせず、ビジネスロジックに集中できます

## Worker Pool コアロジックの概要

コアロジックは `StartWorkerPool`（worker.go）にあります。
主なフロー：

1. `BLPop` で Redis の入力タスクをブロッキング待機します
2. タスクを解析 → goroutine に入ります
3. `sem := make(chan struct{}, concurrency)` で並行上限を実装します
4. Processor を実行します
5. 結果を Redis Hash に書き込みます
6. 実行時間を出力します

擬似フローチャートは以下のように理解できます：

```
while true:
    raw = BLPOP(input_key)
    payload = JSON decode

    acquire semaphore
    go:
        parse(payload.task)
        result = processor()
        HSET(output_key, payload.id, result)
        release semaphore
```

シンプルで堅牢、拡張が容易な設計です。

## カスタムタスク：Parser と Processor

### パーサー（Parser）

例えば、組み込みのリストパーサー（parse list task）：

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

例えば、合計：

```go
func Sum(args []any) (any, error) {
    var sum int
    for _, a := range args {
        sum += int(a.(float64))
    }
    return sum, nil
}
```

画像処理、テキスト分析、外部 API 呼び出しなど、独自の Processor を簡単に実装できます。

## TaskGraph との関係（任意の読み物）

TaskGraph は **Python のタスクグラフ実行フレームワーク** であり、以下が得意です：

* 複雑な DAG の構築
* 依存関係の管理
* 全体的なタスクフローの制御

一方、Go Worker が得意なのは：

* **個々のノードの高パフォーマンスタスクの実行**
* Redis を介した TaskGraph との通信
* 言語に依存しない Worker ノードとしての役割

TaskGraph を総合演出家、Go Worker を素早くステージに上がり機敏に動く実行者と考えることができます。両者は連携することも、独立して動作することもできます。

## サンプル Processor 一覧（processors.go）

これらのサンプルは Worker の使い方を理解するのに役立ち、TaskGraph のクロス言語ノードのデバッグにも便利です：

* `Sum`：合計（例：バッチ計算）
* `Add100`：単一の数値に 100 を加算します
* `Fibonacci`：再帰版フィボナッチ
* `DownloadToFile`：ファイルをローカルにダウンロードします（IO の例）

すべてのソースファイルは processors.go にあります。

## テスト方法

Redis から手動でタスクをプッシュしてテストできます：

```sh
redis-cli LPUSH GoSum[_trans_redis]:input '{"id":"t1","task":[3,4,5]}'
```

次に出力を確認します：

```sh
redis-cli HGET GoSum[_trans_redis]:output t1
```

以下のような結果が表示されます：

```json
{"status":"success","result":12}
```
