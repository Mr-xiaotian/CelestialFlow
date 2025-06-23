package worker

import (
	"encoding/json"
	"fmt"
)

// 示例：把 JSON 解为整数
func ParseNumberTask(raw json.RawMessage) (interface{}, error) {
	var n int
	err := json.Unmarshal(raw, &n)
	return n, err
}

func ParseListTask(data interface{}) ([]interface{}, error) {
	list, ok := data.([]interface{})
	if !ok {
		return nil, fmt.Errorf("task should be a list, got %T", data)
	}
	return list, nil
}
