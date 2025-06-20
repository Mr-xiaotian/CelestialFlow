package main

import (
	"context"

	"github.com/Mr-xiaotian/CelestialFlow/go_worker/worker"

	"github.com/redis/go-redis/v9"
)

func main() {
	ctx := context.Background()

	rdb := redis.NewClient(&redis.Options{
		Addr: "localhost:6379",
		DB:   0,
	})

	worker.StartWorkerPool(
		ctx,
		rdb,
		"GoFibonacci[_trans_redis]:input",  // Redis 中任务输入的 List
		"GoFibonacci[_trans_redis]:output", // Redis 中结果写入的 Hash
		worker.ParseNumberTask,
		worker.Fibonacci,
		4,
	)
}
