package worker

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/redis/go-redis/v9"
)

func StartWorker(
	ctx context.Context,
	rdb *redis.Client,
	inputKey string,
	outputKey string,
	parser TaskParser,
	processor TaskProcessor,
) {
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
			rdb.HSet(ctx, outputKey, "TERMINATION_SIGNAL", `"Worker exiting"`)
			fmt.Println("Termination signal received, exiting.")
			break
		}

		task, err := parser(payload.Task)
		if err != nil {
			fmt.Println("Parse Error:", err)
			continue
		}

		resultVal, err := processor(task)
		if err != nil {
			fmt.Println("Processing Error:", err)
			continue
		}

		resultJSON, _ := json.Marshal(resultVal)
		rdb.HSet(ctx, outputKey, payload.ID, resultJSON)
		fmt.Printf("Processed task %s\n", payload.ID)
	}
}
