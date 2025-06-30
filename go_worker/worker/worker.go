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
				fmt.Println("Processing Error:", err)
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
			fmt.Printf("Processed task: %+v, result: %+v\n", task, resultVal)
		}(payload)
	}
}
