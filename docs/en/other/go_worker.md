# Go Worker

Go Worker is a **lightweight, concurrently scalable, Redis-based task consumer (Worker Pool)**.
Its design goals are only two:

1. **Continuously consume tasks from a Redis task queue**
2. **Execute tasks with controllable concurrency and write results back to Redis**

This component is commonly used as a **cross-language execution node for TaskGraph**:
Python's TaskGraph handles task generation and scheduling logic, while Go Worker focuses on executing compute-intensive or IO-intensive steps. However, the two are completely independent; go-worker can run standalone or be reused by other systems.

## Prerequisites

1. Start the Redis service
Before running `TaskRedis*` series nodes, you need to start the Redis service first.

2. Set environment variables
Then create a .env file in the root directory with the following format:

```env
# .env
# Redis server address
REDIS_HOST=127.0.0.1
# Redis server port
REDIS_PORT=6379
# Redis server password, leave empty if none
REDIS_PASSWORD=your_redis_password
```

3. Set up go_worker

Then open [go_worker main.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/main.go). The Redis host and port will automatically read from environment variables. You only need to set the task input key, result output key, and choose the execution function to use.

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
  "testFibonacci:input",  // Redis input List
  "testFibonacci:output", // Redis output Hash
  worker.ParseListTask,
  worker.Fibonacci,
  4,
)
```

Here we use the settings for running test_redis_ack_0 as an example. The `testFibonacci:input` and `testFibonacci:output` must match the key values of `TaskRedis*` in test_redis_ack_0.

```python
# test_redis_ack_0
redis_sink = TaskRedisTransport(key="testFibonacci:input", host=redis_host, password=redis_password)
redis_ack = TaskRedisAck(key="testFibonacci:output", host=redis_host, password=redis_password)
```

Also select the Go function you want to use in [go_worker processor.go](https://github.com/Mr-xiaotian/CelestialFlow/blob/main/go_worker/worker/processor.go).

4. Run go_worker

Then run:

```bash
make run_go_worker
```

go_worker starts and begins listening to the Redis queue. At this point, you can run pytest normally.

## Features

* **Worker Pool concurrent execution**, using `chan` + `WaitGroup` to control maximum concurrency
  (see source in `StartWorkerPool`)
* **Automatic reconnection with exponential backoff**, automatically recovers even when Redis is unstable
* **Generic task structure**: Tasks are packed in JSON and sent to Redis
  (see `TaskPayload` structure)
* **Pluggable Parser / Processor**: Users can freely define task parsing and processing methods
* **Results written to Redis Hash**, making it easy for external systems to query task execution status
* Provides several **example Processors (Sum / Add100 / Fibonacci / DownloadToFile)**
  (see processors.go)

## Task Structure (TaskPayload)

Each task is written to a Redis list in JSON format:

```json
{
  "id": "task-001",
  "task": [1, 2, 3]
}
```

Go Worker retrieves the JSON, then:

* Uses the Parser to convert the task field into the type expected by the Processor
* The Processor handles the computation and returns the result
* The final result is written to a Redis Hash: `HSET output_key id {...}`

Data structure definition (types.go):

```go
type TaskPayload struct {
	ID   string `json:"id"`
	Task any    `json:"task"`
}
```

Parser and Processor signatures:

```go
type TaskParser func(any) ([]any, error)
type TaskProcessor func([]any) (any, error)
```

This design allows you to:

* Freely extend task formats
* Let Processors focus on business logic without worrying about JSON and Redis

## Worker Pool Core Logic

The core logic resides in `StartWorkerPool` (worker.go).
Main flow:

1. `BLPop` blocks waiting for Redis input tasks
2. Parse task → enter goroutine
3. Use `sem := make(chan struct{}, concurrency)` to implement concurrency limit
4. Execute Processor
5. Write result to Redis Hash
6. Print execution time

The pseudo-flowchart can be understood as:

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

Simple, robust, and easy to extend.

## Custom Tasks: Parser and Processor

### Parser

For example, the built-in list parser (parse list task):

```go
func ParseListTask(data any) ([]any, error) {
    list, ok := data.([]any)
    if !ok {
        return nil, fmt.Errorf("task should be a list, got %T", data)
    }
    return list, nil
}
```

### Processor (Business Logic)

For example, sum:

```go
func Sum(args []any) (any, error) {
    var sum int
    for _, a := range args {
        sum += int(a.(float64))
    }
    return sum, nil
}
```

You can easily implement your own processor for image processing, text analysis, external API calls, etc.

## Relationship with TaskGraph (Optional Reading)

TaskGraph is a **Python task graph execution framework**, good at:

* Building complex DAGs
* Managing dependencies
* Controlling overall task flow

While Go Worker excels at:

* Executing **high-performance tasks for individual nodes**
* Communicating with TaskGraph via Redis
* Serving as a language-agnostic Worker node

You can think of TaskGraph as the director, and Go Worker as the quick, agile performer who takes the stage. They can work together or independently.

## Example Processor List (processors.go)

These examples help you understand how to use the Worker and are also useful for debugging cross-language nodes in TaskGraph:

* `Sum`: Summation (example: batch computation)
* `Add100`: Add 100 to a single number
* `Fibonacci`: Recursive Fibonacci
* `DownloadToFile`: Download file to local disk (IO example)

All source files are in processors.go.

## Testing

You can manually push a task via Redis for testing:

```sh
redis-cli LPUSH GoSum[_trans_redis]:input '{"id":"t1","task":[3,4,5]}'
```

Then check the output:

```sh
redis-cli HGET GoSum[_trans_redis]:output t1
```

You should see something like:

```json
{"status":"success","result":12}
```
