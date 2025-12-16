# Go Worker

Go Worker 是一个 **轻量级、可并发扩展、基于 Redis 的任务消费者（Worker Pool）**。
它的设计目标只有两个：

1. **从 Redis 的任务队列中持续消费任务**
2. **以可控的并发度执行任务，并将结果写回 Redis**

这个组件常作为 **TaskGraph 的跨语言执行节点** 使用：
Python 的 TaskGraph 负责生成任务、决定调度逻辑，而 Go Worker 专注于执行计算密集或 IO 密集的步骤。不过，两者完全独立；go-worker 可以单独运行，也可以被其他系统复用。

## 前期设置

1. 启动 Redis 服务
在运行`TaskRedis*`系节点时, 需要先启动 Redis 服务

2. 设置环境变量
然后在根目录下建立一个.env文件, 按以下格式填入:

```env
# .env
# Redis 服务地址
REDIS_HOST=127.0.0.1
# Redis 服务端口
REDIS_PORT=6379
# Redis 服务密码, 没有则留空
REDIS_PASSWORD=your_redis_password
```

3. 设置 go_worker

然后打开[go_worker main.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/main.go)。其中redis的host与port会自动读取环境变量中的设置, 我们需要设置的只有任务输入的key与结果输出的key, 以及选择要使用的执行函数。

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
  "testFibonacci:input",  // Redis 中任务输入的 List
  "testFibonacci:output", // Redis 中结果写入的 Hash
  worker.ParseListTask,
  worker.Fibonacci,
  4,
)
```

这里我们以运行 test_redis_ack_0 时的设置为例, 其中的`testFibonacci:input`与`testFibonacci:output`需要与 test_redis_ack_0 中 `TaskRedis*` dekey值相同。

```python
# test_redis_ack_0
redis_sink = TaskRedisSink(key="testFibonacci:input", host=redis_host, password=redis_passward)
redis_ack = TaskRedisAck(key="testFibonacci:output", host=redis_host, password=redis_passward)
```

同时在[go_worker processor.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/worker/processor.go)中选择你要使用的 Go 函数。

4. 运行go_worker

然后运行

```bash
make run_go_worker
```

go_worker启动并开始监听 Redis 队列, 此时可以正常运行pytest。

## ✨ 功能特性

* **Worker Pool 并发执行**，使用 `chan` + `WaitGroup` 控制最大并发
  （源码见 `StartWorkerPool` ）
* **自动重连与指数退避机制（backoff）**，即使 Redis 不稳定也能自动恢复
* **任务结构通用化**：任务由 JSON 打包传入 Redis
  （结构见 `TaskPayload` ）
* **Parser / Processor 可插拔**：用户可自由定义任务解析方式与处理方式
* **结果写回 Redis Hash**，便于外部系统查询任务执行情况
* 提供数个 **示例 Processor（Sum / Add100 / Fibonacci / DownloadToFile）**
  （见 processors.go ）

## 📦 任务结构说明（TaskPayload）

每条任务以 JSON 形式写入 Redis list：

```json
{
  "id": "task-001",
  "task": [1, 2, 3]
}
```

Go Worker 会先取出 JSON，然后：

* 使用 Parser 将 task 字段转换为 Processor 想要的类型
* Processor 负责返回计算结果
* 最终结果写入 Redis Hash：`HSET output_key id {...}`

数据结构定义如下（types.go）：

```go
type TaskPayload struct {
	ID   string `json:"id"`
	Task any    `json:"task"`
}
```

Parser 与 Processor 的签名：

```go
type TaskParser func(any) ([]any, error)
type TaskProcessor func([]any) (any, error)
```

这种设计允许你：

* 让任务格式自由扩展
* 让 Processor 专注于业务逻辑，不关心 JSON 与 Redis

## 🏗 Worker Pool 核心逻辑简述

核心逻辑位于 `StartWorkerPool`（worker.go） 。
主要流程：

1. `BLPop` 阻塞等待 Redis 输入任务
2. 解析任务 → 进入 goroutine
3. 使用 `sem := make(chan struct{}, concurrency)` 实现并发上限
4. 执行 Processor
5. 将结果写入 Redis Hash
6. 打印执行耗时

伪流程图可以理解为：

```
while true:
    raw = BLPOP(input_key)
    payload = JSON 解码

    acquire semaphore
    go:
        parse(payload.task)
        result = processor()
        HSET(output_key, payload.id, result)
        release semaphore
```

设计简单、稳健、易扩展。

## 🧩 自定义任务：Parser 与 Processor

### 解析器（Parser）

例如官方给的列表解析器（parse list task）：

```go
func ParseListTask(data any) ([]any, error) {
    list, ok := data.([]any)
    if !ok {
        return nil, fmt.Errorf("task should be a list, got %T", data)
    }
    return list, nil
}
```

### Processor（业务逻辑）

例如求和：

```go
func Sum(args []any) (any, error) {
    var sum int
    for _, a := range args {
        sum += int(a.(float64))
    }
    return sum, nil
}
```

你可以轻松实现自己的 processor，例如图像处理、文本分析、外部接口调用等。

## 🧵 与 TaskGraph 的关系（可选阅读）

TaskGraph 是一个 **Python 任务图执行框架**，擅长：

* 构建复杂 DAG
* 管理依赖关系
* 控制整体任务流程

而 Go Worker 则擅长：

* 执行**单个节点的高性能任务**
* 在 Redis 中与 TaskGraph 通信
* 作为语言无关的 Worker 节点

你可以把 TaskGraph 想象成总导演，而 Go Worker 是能快速上台、动作敏捷的执行者。二者可配合，也可独立。

## 📁 示例 Processor 列表（processors.go）

这些示例方便你理解 Worker 的使用方法，也方便 TaskGraph 调试跨语言节点：

* `Sum`：求和（示例：批量计算）
* `Add100`：对单数字加 100
* `Fibonacci`：递归版斐波那契
* `DownloadToFile`：下载文件到本地（IO 示例）

全部源文件见 processors.go 。

## 🧪 测试方式

你可以用 Redis 手动 push 一个任务测试：

```sh
redis-cli LPUSH GoSum[_trans_redis]:input '{"id":"t1","task":[3,4,5]}'
```

然后在输出：

```sh
redis-cli HGET GoSum[_trans_redis]:output t1
```

能看到类似：

```json
{"status":"success","result":12}
```
