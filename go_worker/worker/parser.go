package worker

import (
	"encoding/json"
	"fmt"
)

// 示例：把 JSON 解为整数
func ParseNumberTask(raw json.RawMessage) (any, error) {
	var n int
	err := json.Unmarshal(raw, &n)
	return n, err
}

func ParseListTask(data any) ([]any, error) {
	list, ok := data.([]any)
	if !ok {
		return nil, fmt.Errorf("task should be a list, got %T", data)
	}
	return list, nil
}
