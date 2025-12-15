package main

import (
	"context"
	"fmt"
	"os"

	"github.com/Mr-xiaotian/CelestialFlow/go_worker/worker"

	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
)

func main() {
	err := godotenv.Load()
	if err != nil {
		fmt.Println("No .env file found, using system env")
	}

	redisHost := os.Getenv("REDIS_HOST")
	redisPort := os.Getenv("REDIS_PORT")
	redisPassword := os.Getenv("REDIS_PASSWORD")

	if redisHost == "" || redisPort == "" {
		panic("REDIS_HOST or REDIS_PORT not set")
	}

	ctx := context.Background()

	rdb := redis.NewClient(&redis.Options{
		Addr:     redisHost + ":" + redisPort,
		Password: redisPassword,
		DB:       0,
	})

	fmt.Println("Go Worker Start")
	defer fmt.Println("Go Worker End")

	worker.StartWorkerPool(
		ctx,
		rdb,
		"GoSum[_trans_redis]:input",  // Redis 中任务输入的 List
		"GoSum[_trans_redis]:output", // Redis 中结果写入的 Hash
		worker.ParseListTask,
		worker.Sum,
		4,
	)
}
