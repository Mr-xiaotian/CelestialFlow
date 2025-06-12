package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"

	"github.com/redis/go-redis/v9"
)

// Worker pool 并发处理
func StartWorkerPool(
	ctx context.Context,
	rdb *redis.Client,
	inputKey string,
	outputKey string,
	parser TaskParser,
	processor TaskProcessor,
	concurrency int, // 并发上限
) {
	var wg sync.WaitGroup
	sem := make(chan struct{}, concurrency) // 控制并发数

	for {
		result, err := rdb.BLPop(ctx, 0, inputKey).Result()
		if err != nil {
			fmt.Println("BLPop Error:", err)
			continue
		}

		var payload TaskPayload
		err = json.Unmarshal([]byte(result[1]), &payload)
		if err != nil {
			fmt.Println("JSON Parse Error:", err)
			continue
		}

		if payload.ID == "TERMINATION_SIGNAL" {
			// 等所有 goroutine 完成
			wg.Wait()
			rdb.HSet(ctx, outputKey, "TERMINATION_SIGNAL", `"Worker exiting"`)
			fmt.Println("Termination signal received, exiting.")
			break
		}

		sem <- struct{}{} // 获取并发令牌
		wg.Add(1)
		go func(p TaskPayload) {
			defer func() {
				<-sem // 释放令牌
				wg.Done()
			}()

			task, err := parser(p.Task)
			if err != nil {
				fmt.Println("Parse Error:", err)
				return
			}

			resultVal, err := processor(task)
			if err != nil {
				fmt.Println("Processing Error:", err)
				return
			}

			resultJSON, _ := json.Marshal(resultVal)
			rdb.HSet(ctx, outputKey, p.ID, resultJSON)
			fmt.Printf("Processed task %s\n", p.ID)
		}(payload)
	}
}
