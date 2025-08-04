package worker

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"

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
		redisData, err := rdb.BLPop(ctx, 0, inputKey).Result()
		if err != nil {
			fmt.Println("BLPop Error:", err)
			continue
		}

		var payload TaskPayload
		err = json.Unmarshal([]byte(redisData[1]), &payload)
		if err != nil {
			fmt.Println("JSON Parse Error:", err)
			continue
		}

		sem <- struct{}{} // 获取并发令牌
		wg.Add(1)

		go func(p TaskPayload) {
			defer func() {
				<-sem // 释放令牌
				wg.Done()
			}()

			startTime := time.Now() // 记录开始时间

			task, err := parser(p.Task)
			if err != nil {
				fmt.Println("Parse Error:", err)
				resp := map[string]any{
					"status": "error",
					"error":  fmt.Sprintf("Parse error: %v", err),
				}
				if jsonResp, e := json.Marshal(resp); e == nil {
					_ = rdb.HSet(ctx, outputKey, p.ID, jsonResp)
				}
				return
			}

			resultVal, err := processor(task)
			if err != nil {
				fmt.Printf("[ERROR] Task: %+v, Error: %v\n", task, err)
				resp := map[string]any{
					"status": "error",
					"error":  fmt.Sprintf("Processing error: %v", err),
				}
				if jsonResp, e := json.Marshal(resp); e == nil {
					_ = rdb.HSet(ctx, outputKey, p.ID, jsonResp)
				}
				return
			}

			resp := map[string]any{
				"status": "success",
				"result": resultVal,
			}
			if jsonResp, err := json.Marshal(resp); err == nil {
				_ = rdb.HSet(ctx, outputKey, p.ID, jsonResp)
			}

			endTime := time.Now() // 记录结束时间
			duration := endTime.Sub(startTime)
			fmt.Printf("[SUCCESS] Task: %+v, Result: %+v, Duration: %s\n", task, resultVal, duration)
		}(payload)
	}
}
